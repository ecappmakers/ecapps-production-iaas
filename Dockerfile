# 1. Allow JRE Version to be passed as an Argument
ARG JRE_VERSION=11
# FIX: Use ${} syntax, not %%
FROM azul/zulu-openjdk:${JRE_VERSION}-jre

# 2. Allow Tomcat Version to be passed
ARG TOMCAT_MAJOR=10
ARG TOMCAT_VERSION=10.1.18

ENV CATALINA_HOME=/usr/local/tomcat
ENV PATH=$CATALINA_HOME/bin:$PATH

# Install Tomcat
RUN apt-get update && apt-get install -y wget tar && rm -rf /var/lib/apt/lists/*
# FIX: Use ${} syntax for all variables below
RUN wget -q https://archive.apache.org/dist/tomcat/tomcat-${TOMCAT_MAJOR}/v${TOMCAT_VERSION}/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz && \
    mkdir -p ${CATALINA_HOME} && \
    tar -xf apache-tomcat-${TOMCAT_VERSION}.tar.gz -C ${CATALINA_HOME} --strip-components=1 && \
    rm apache-tomcat-${TOMCAT_VERSION}.tar.gz

RUN rm -rf ${CATALINA_HOME}/webapps/*

EXPOSE 8080
CMD ["catalina.sh", "run"]
