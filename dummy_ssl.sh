openssl genrsa -des3 -passout pass:utveckling -out server.key 1024
openssl rsa -in server.key -passin pass:utveckling -out server.key
openssl req -new -key server.key -out server.csr \
-subj "/C=SE/ST=./L=./O=./OU=./CN=./emailAddress=."
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
rm server.csr
