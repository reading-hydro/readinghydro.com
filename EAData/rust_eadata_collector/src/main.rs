use aws_config::meta::region::RegionProviderChain;
use aws_sdk_secretsmanager as secretsmanager;
use chrono::{DateTime, Utc};
use reqwest::Client;
use serde::Deserialize;
use serde_json::Value;
use std::env;
use tokio_postgres::NoTls;

#[derive(Deserialize)]
struct Item {
    dateTime: String,
    value: f64,
}

async fn get_aws_secret(secret_name: &str) -> anyhow::Result<Value> {
    let region_provider = RegionProviderChain::default_provider().or_else("eu-west-2");
    let config = aws_config::from_env().region(region_provider).load().await;
    let client = secretsmanager::Client::new(&config);
    let resp = client
        .get_secret_value()
        .secret_id(secret_name)
        .send()
        .await?;

    if let Some(s) = resp.secret_string() {
        let v: Value = serde_json::from_str(s)?;
        Ok(v)
    } else {
        Err(anyhow::anyhow!("No secret string returned"))
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init();
    println!("Starting update of EA data tables");

    // Try to read DB config from environment, otherwise fall back to AWS Secrets Manager
    let db_host = env::var("DB_HOST").ok();
    let db_port = env::var("DB_PORT").ok();
    let db_user = env::var("DB_USER").ok();
    let db_password = env::var("DB_PASSWORD").ok();
    let db_name = env::var("DB_NAME").ok();

    let (db_host, db_port, db_user, db_password, db_name) = if db_host.is_some()
        && db_port.is_some()
        && db_user.is_some()
        && db_password.is_some()
        && db_name.is_some()
    {
        (
            db_host.unwrap(),
            db_port.unwrap(),
            db_user.unwrap(),
            db_password.unwrap(),
            db_name.unwrap(),
        )
    } else {
        let secret = get_aws_secret("RdgHydroServerSecrets").await?;
        let get = |k: &str| -> anyhow::Result<String> {
            Ok(secret
                .get(k)
                .and_then(|v| v.as_str())
                .ok_or_else(|| anyhow::anyhow!("Missing key"))?
                .to_string())
        };
        (
            get("DB_HOST")?,
            get("DB_PORT")?,
            get("DB_USER")?,
            get("DB_PASSWORD")?,
            get("DB_NAME")?,
        )
    };

    let db_port: u16 = db_port.parse()?;

    let conn_str = format!(
        "host={} port={} user={} password={} dbname={}",
        db_host, db_port, db_user, db_password, db_name
    );

    let (client, connection) = tokio_postgres::connect(&conn_str, NoTls).await?;
    // Spawn the connection task to drive the connection
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("connection error: {}", e);
        }
    });

    // Get last entry
    let row = client
        .query_opt("SELECT entrytime FROM public.eadata ORDER BY entrytime DESC LIMIT 1", &[])
        .await?;

    let last_entry: DateTime<Utc> = if let Some(r) = row {
        let dt: DateTime<Utc> = r.get::<usize, DateTime<Utc>>(0);
        println!("Last data entry is currently: {}", dt);
        dt
    } else {
        let now = Utc::now();
        println!("No existing entry found, using now: {}", now);
        now
    };

    let myds3 = last_entry.format("%Y-%m-%d").to_string();
    let myds4 = Utc::now().format("%Y-%m-%d").to_string();

    let ea_api_url = format!("https://environment.data.gov.uk/flood-monitoring/id/measures/2200TH-flow--Mean-15_min-m3_s/readings?startdate={}&enddate={}&_sorted&_limit=3000", myds3, myds4);

    let http = Client::builder().timeout(std::time::Duration::from_secs(20)).build()?;
    let resp = http.get(&ea_api_url).send().await?;
    if !resp.status().is_success() {
        eprintln!("Error getting EA data: {}", resp.status());
        return Ok(());
    }

    let body: Value = resp.json().await?;
    let items = body.get("items").and_then(|v| v.as_array()).cloned().unwrap_or_default();

    let mut rows_added = 0i64;
    for it in items {
        if let Ok(item) = serde_json::from_value::<Item>(it) {
            if let Ok(dt) = DateTime::parse_from_rfc3339(&item.dateTime) {
                let dt_utc: DateTime<Utc> = dt.with_timezone(&Utc);
                if dt_utc > last_entry && item.value > 0.0 {
                    client
                        .execute(
                            "INSERT INTO public.eadata (entrytime, flow) VALUES ($1, $2)",
                            &[&dt_utc, &item.value],
                        )
                        .await?;
                    rows_added += 1;
                }
            }
        }
    }

    println!("Rows added are: {}", rows_added);

    Ok(())
}
