ARG JRE_VERSION=11
FROM azul/zulu-openjdk:%JRE_VERSION%-jre

ARG TOMCAT_MAJOR=10
ARG TOMCAT_VERSION=10.1.18

ENV CATALINA_HOME=/usr/local/tomcat
ENV PATH=$CATALINA_HOME/bin:$PATH

RUN apt-get update && apt-get install -y wget tar && rm -rf /var/lib/apt/lists/*
RUN wget -q https://archive.apache.org/dist/tomcat/tomcat-%TOMCAT_MAJOR%/v%TOMCAT_VERSION%/bin/apache-tomcat-%TOMCAT_VERSION%.tar.gz && \
    mkdir -p %CATALINA_HOME% && \
    tar -xf apache-tomcat-%TOMCAT_VERSION%.tar.gz -C %CATALINA_HOME% --strip-components=1 && \
    rm apache-tomcat-%TOMCAT_VERSION%.tar.gz

RUN rm -rf %CATALINA_HOME%/webapps/*

EXPOSE 8080
CMD ["catalina.sh", "run"]
