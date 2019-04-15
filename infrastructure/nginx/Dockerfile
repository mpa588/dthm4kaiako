FROM uccser/nginx-with-gulp:1.15.8

ADD dthm4kaiako/package.json /app/
RUN npm install
ADD ./dthm4kaiako/ /app/
RUN chmod 755 /app/
ADD infrastructure/nginx/nginx.conf /etc/nginx/nginx.conf
