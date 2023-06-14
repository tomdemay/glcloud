FROM php:7.4-apache

# Create label we can query to see if this image is using the 
#   correct private_ip_address
LABEL MYSQL_IP_ADDRESS={private_ip_address}

# Set the working directory inside the container
WORKDIR /var/www/html

# Copy the application files to the container
COPY ./projects/devops/assessment/crud/ .

# Modify the database configuration file
RUN sed -i 's/"localhost";/"{private_ip_address}";/' ./backend/database.php \
    && sed -i 's/"";/"{mysql_root_password}";/' ./backend/database.php \
    && sed -i 's/"user";/"{mysql_database}";/' ./backend/database.php

# Install the mysqli extension
RUN docker-php-ext-install mysqli

# Expose the desired port (e.g., 80 for HTTP)
EXPOSE 80/tcp
