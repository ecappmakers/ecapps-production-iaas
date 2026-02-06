FROM php:8.1-apache

# Install required extensions
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Enable Apache modules
RUN a2enmod headers rewrite

# Set working directory
WORKDIR /var/www/html

# Start Apache
CMD ["apache2-foreground"]
