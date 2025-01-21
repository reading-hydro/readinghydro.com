package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"ioutil"
	"log"
	"net/http"
	"strconv"
	"time"

	aws "github.com/MarkStanley/awssecrets"
	_ "github.com/lib/pq"
)

// PLCData - partial struct for a Hydro Message
type EAData struct {
	entrytime time.Time `json:"entrytime"`
	flow      float32   `json:"flow"`
}

func main() {
	aws.GetAllSecrets(SecretsName)

	ServerPort = aws.GetSecret("HYDRO_API_SERVER_PORT")

	DbHost := aws.GetSecret("DB_HOST")
	DbPort, _ := strconv.ParseInt(aws.GetSecret("DB_PORT"), 10, 0)
	DbUser := aws.GetSecret("DB_USER")
	DbPassword := aws.GetSecret("DB_PASSWORD")
	DbName := aws.GetSecret("DB_NAME")
	CertDir := aws.GetSecret("CERT_DIR")

	// Connect to the database
	connString := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable", DbHost, DbPort, DbUser, DbPassword, DbName)
	//log.Println(connString)
	db, err := sql.Open("postgres", connString)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		panic(err)
	}

	//database form is:
	//    CREATE TABLE public.eadata (time timestamp NOT NULL, flow double precision);
	//	  ALTER TABLE public.eadata OWNER TO hydrodbuser;
	//	  ALTER TABLE ONLY public.eadata ADD CONSTRAINT eadata_pkey PRIMARY KEY (time);

	// Read the database and find the time of the last data value
	var Last EAData
	err = db.QueryRow("SELECT time FROM public.eadata ORDER BY entrytime DESC").Scan(&Last.entrytime, &Last.flow)
	if err != nil {
		log.Println(fmt.Errorf("Error retrieving current EA data: %v", err))
		return
	}

	// Read the EA data for the data items since the last data value

	// Fetch data from the API
	myds3 := Last.entrytime.Format("2001-01-02")
	myds4 := time.Now().Format("2001-01-02")
	EAapiURL := "https://environment.data.gov.uk/flood-monitoring/id/measures/2200TH-flow--Mean-15_min-m3_s/readings?startdate=" + myds3 + "&enddate=" + myds4 + "&_sorted&_limit=3000"
	response, err := http.Get(EAapiURL)
	if err != nil {
		log.Fatalf("Error fetching data from API: %v", err)
	}
	defer response.Body.Close()

	if response.StatusCode != http.StatusOK {
		log.Fatalf("API returned non-OK status: %s", response.Status)
	}

	// Read response body
	bodyBytes, err := ioutil.ReadAll(response.Body)
	if err != nil {
		log.Fatalf("Error reading response body: %v", err)
	}

	// Parse JSON data
	var items []Item
	err = json.Unmarshal(bodyBytes, &items)
	if err != nil {
		log.Fatalf("Error parsing JSON data: %v", err)
	}

	// Enter any new data into the database

}
