#!/usr/bin/env bash

acme_tiny_path="/root/acme_tiny"
letsencrypt_dir="/etc/letsencrypt"
today=$(date +"%Y_%m_%d")

"${acme_tiny_path}/acme_tiny.py" --account-key "${letsencrypt_dir}/account.key" --csr "${letsencrypt_dir}/domain.csr" --acme-dir /var/www/challenges/ > "${letsencrypt_dir}/signed_chain_${today}.crt"

file_type=$(file "${letsencrypt_dir}/signed_chain_${today}.crt" | awk -F ': ' '{print $2}')

if [[ $file_type == "PEM certificate" ]]; then
    echo "New certificate is valid - configuring..."
    ln -s --force "${letsencrypt_dir}/signed_chain_${today}.crt" "${letsencrypt_dir}/signed_chain.crt"
    docker restart nginx
else
    echo "New certificate is not valid - keeping old one!"
fi
