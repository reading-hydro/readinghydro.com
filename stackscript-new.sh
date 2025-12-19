#!/usr/bin/env bash 

## WordPress Settings
# <UDF name="site_title" label="Website Title" default="Title" example="My Blog">
# <UDF name="wordpress_name" label="WordPress Name" default="wordpress">
# <UDF name="soa_email_address" label="E-Mail Address" example="Your email address">
# <UDF name="wp_admin" label="Admin Username" example="Username for your WordPress admin panel">

## Linode/SSH Security Settings
#<UDF name="username" label="The limited sudo user to be created for the Linode" default="">
#<UDF name="password" label="The password for the limited sudo user" example="an0th3r_s3cure_p4ssw0rd" default="">
#<UDF name="pubkey" label="The SSH Public Key that will be used to access the Linode" default="">
#<UDF name="disable_root" label="Disable root access over SSH?" oneOf="Yes,No" default="No">

## Domain Settings
#<UDF name="token_password" label="Your Linode API token. This is needed to create your WordPress server's DNS records" default="">
#<UDF name="subdomain" label="Subdomain" example="The subdomain for the DNS record: www (Requires Domain)" default="">
#<UDF name="domain" label="Domain" example="The domain for the DNS record: example.com (Requires API token)" default="">
#<UDF name="send_email" label="Would you like to be able to send password reset emails for WordPress? (Requires domain)" oneOf="Yes,No" default="Yes">


## Enable logging
exec > >(tee /dev/ttyS0 /var/log/stackscript.log) 2>&1
set -xo pipefail
## Import the Bash StackScript Library
source <ssinclude StackScriptID=1>

### Installations
function wp_oca_lamp_stack {
    local -r dbroot_password="$1"
    local -r wordpress_name="$2"
    local -r fqdn="$3"
    local -r ip_address="$(system_primary_ip)"

    # Set MySQL root password
    mysql_root_preinstall

    # Install MySQL/MariaDB
    apt install -y mariadb-server
    # Secure MySQL install
    run_mysql_secure_installation

    # Install PHP
    system_install_package php php-curl php-common openssl php-imagick php-json php-mbstring php-mysql pcre2-utils php-xml php-zip apache2 unzip sendmail-bin sendmail
    PHP_VERSION=$(php -r "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;")
    ### Configurations

    # MySQL
    mysql -uroot -p"$dbroot_password" -e "CREATE DATABASE wordpressdb"
    mysql -uroot -p"$dbroot_password" -e "GRANT ALL ON wordpressdb.* TO 'wordpress'@'localhost' IDENTIFIED BY '${DB_PASSWORD}'";
    mysql -uroot -p"$dbroot_password" -e "FLUSH PRIVILEGES";

    # Apache
    rm /var/www/html/index.html
    mkdir -p /var/www/$wordpress_name

    # Configuration of virtualhost file, disables xmlrpc
    # Sets up a virtualhost for either the domain or the IP address
        cat <<END > /etc/apache2/sites-available/$wordpress_name.conf
<Directory /var/www/$wordpress_name/>
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
<VirtualHost $fqdn:80>
    ServerName $fqdn
    ServerAdmin webmaster@$fqdn
    DocumentRoot /var/www/$wordpress_name/
    ErrorLog /var/log/apache2/wordpress/error.log
    CustomLog /var/log/apache2/wordpress/access.log combined
    <files xmlrpc.php>
    order allow,deny
    deny from all
    </files>
</VirtualHost>
END
    # Create log files for WordPress
    mkdir -p /var/log/apache2/wordpress
    touch /var/log/apache2/wordpress/error.log
    touch /var/log/apache2/wordpress/access.log

    # Enable the needed Apache modules
    a2enmod proxy_fcgi setenvif rewrite

    # Enable Keepalives
    sed -ie "s/KeepAlive Off/KeepAlive On/g" /etc/apache2/apache2.conf
}


function wordpress_oca_install {
    local -r db_password="$1"
    local -r wordpress_name="$2"
    local -r fqdn="$3"
    local -r site_title="$4"
    local -r wpadmin="$5"
    local -r wp_password="$6"
    local -r soa_email_address="$7"
    local -r ip_address="$(system_primary_ip)"


    # Install WordPress useing the WP-CLI tool
    curl -sLo wp-cli.phar https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
    mv wp-cli.phar /usr/local/bin/wp
    chmod 755 /usr/local/bin/wp

    # Configure WordPress site
    cd /var/www/$domain || exit 1

    wp core download --allow-root

    wp core config --allow-root \
        --dbhost=localhost \
        --dbname="${wordpress_name}db" \
        --dbuser=wordpress \
        --dbpass="$db_password"

    # Configure the WordPress site to use the domain
        wp core install --allow-root \
            --url="$fqdn" \
            --title="$site_title" \
            --admin_user="$wpadmin" \
            --admin_email="$soa_email_address" \
            --admin_password="$wp_password" \
            --path="/var/www/$wordpress_name/"

    # Set ownership of the WordPress installation folder
    chown www-data:www-data -R /var/www/$wordpress_name/

    # Configure PHP to play nicely
    sed -i s/post_max_size\ =.*/post_max_size\ =\ 100M/ /etc/php/$PHP_VERSION/apache2/php.ini
    sed -i s/upload_max_filesize\ =.*/upload_max_filesize\ =\ 100M/ /etc/php/$PHP_VERSION/apache2/php.ini
    sed -i s/memory_limit\ =.*/memory_limit\ =\ 256M/ /etc/php/$PHP_VERSION/apache2/php.ini

    # Cron for WordPress updates
    echo "0 1 * * * '/usr/local/bin/wp core update --allow-root --path=/var/www/$wordpress_name/' > /dev/null 2>&1" >> wpcron
    crontab wpcron
    rm wpcron

    # Disable the default virtual host
    a2dissite 000-default.conf
    a2ensite $wordpress_name.conf

    # Fix for error stating that 
    # Restart services
    systemctl restart mariadb
    systemctl restart apache2
}

function firewalls {
    # Open firewall ports
    ufw allow http
    ufw allow https
    ufw allow 25
    ufw allow 587
    ufw allow 110
} 

function ssl {
    apt install certbot python3-certbot-apache -y
    certbot_ssl "$FQDN" "$SOA_EMAIL_ADDRESS" 'apache'
}

function save_configuration {

    cat <<END > /var/log/wordpress_installation_info.txt
Server settings
IP Address: $IP
IPv6 Address: $IP6
WordPress Installation
WordPress Name: $WORDPRESS_NAME
Fully Qualified Domain Name: $FQDN
Website Title: $SITE_TITLE
E-Mail Address: $SOA_EMAIL_ADDRESS
Admin Username: $WP_ADMIN
Admin Password: $WP_PASSWORD
MySQL root Password: $DBROOT_PASSWORD
WordPress Database Password: $DB_PASSWORD
PHP Version: $PHP_VERSION
WordPress Database Name: $DB_NAME
WordPress Version: $(wp core version --allow-root --path="/var/www/${WORDPRESS_NAME}/")
Linode/SSH Security Settings
Username: $USERNAME
Password: $PASSWORD
SSH Public Key: $PUBKEY
Disable Root Access: $DISABLE_ROOT
Domain Settings
Linode API Token: $TOKEN_PASSWORD
Subdomain: $SUBDOMAIN
Domain: $DOMAIN
Send E-Mail: $SEND_EMAIL
END

}
### Main Script
# Set hostname, run updates
get_started \"$SUBDOMAIN\" \"$DOMAIN\" \"$IP\"

# Get the Linode's IP address
readonly IP=$(system_primary_ip)
readonly IP6=$(system_primary_ipv6)

# Generate passwords
readonly WP_PASSWORD=randomString 16
readonly DBROOT_PASSWORD=randomString 16
readonly DB_PASSWORD=randomString 16
readonly DB_NAME=\"${WORDPRESS_NAME}db\"

#set timezone and configure NTP
system_set_timezone 'UTC'
system_configure_ntp

# Setup the sudo user, SSH keys, and disable root if needed
if [ \"$USERNAME\" ]; then
    # Create the user and add it to the 'sudo' group
    user_add_sudo \"$USERNAME\" \"$PASSWORD\" && {
        [ \"$DISABLE_ROOT\" == 'Yes' ] && ssh_disable_root
        [ \"$PUBKEY\" ] && user_add_pubkey \"$USERNAME\" \"$PUBKEY\"

        # Restart SSH to apply the changes
        systemctl restart ssh
    }
fi

# Configure the firewall and Security
configure_ufw_firewall 22,80,443,8883,9445,9446
enable_fail2ban
automatic_security_updates

### Domain and FQDN Configuration
if [ \"$DOMAIN\" ]; then
    # Determine the Linode's FQDN
    if [ \"$SUBDOMAIN\" == \"\" ];
        then readonly FQDN=\"$DOMAIN\"
        else readonly FQDN=\"${SUBDOMAIN}.${DOMAIN}\"
    fi
fi

wp_oca_lamp_stack \"$DBROOT_PASSWORD\" \"$WORDPRESS_NAME\" \"$FQDN\"

wordpress_oca_install \"$DBROOT_PASSWORD\" \"$WORDPRESS_NAME\" \"$FQDN\" \
         \"$SITE_TITLE\" \"$WP_ADMIN\" \"$WP_PASSWORD\" \"$SOA_EMAIL_ADDRESS\"

save_configuration