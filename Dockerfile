# syntax=docker/dockerfile:1
FROM eclipse-temurin:17-jdk-jammy AS build
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.m2 sh ./mvnw -B -ntp verify

FROM eclipse-temurin:17-jre-jammy AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 bookstore \
    && useradd --uid 10001 --gid bookstore --no-create-home bookstore
WORKDIR /app
COPY --from=build --chown=bookstore:bookstore /workspace/target/bookstore-0.0.1-SNAPSHOT.jar app.jar
USER bookstore
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
