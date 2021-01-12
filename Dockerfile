FROM python:3.8.5

# Labels
LABEL maintainer="damian.mcdonald"
LABEL org.label-schema.schema-version="1.0.0"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="composer-dag-dsl"
LABEL org.label-schema.description="Python API that provides dag validation, deployment and triggering functionality within a GCP Cloud composer environment"
LABEL org.label-schema.url="https://github.com/damianmcdonald/composer-dag-dsl"
LABEL org.label-schema.vcs-url="https://github.com/damianmcdonald/composer-dag-dsl"
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.vendor="WSO1"
LABEL org.label-schema.version=$BUILD_VERSION
LABEL org.label-schema.docker.cmd="docker run -p 80:80 --env-file=env_composer composer-dag-dsl:1.0.0"

# Update the images binaries and ensure that git is installed
RUN apt update -y && apt install git -y

# copy the composer source code to /app/composer/ on the image
COPY composer/ /app/composer/

# copy requirements-linux.txt to /app/requirements-linux.txt on the image
COPY requirements-linux.txt /app/requirements-linux.txt

# run the pip install command in order to install all of the required libraries and their dependencies
RUN cd /app && pip install -r requirements-linux.txt

# execute the command to launch gunicorn which exposes the public API
CMD ["bash", "-c", "cd /app && gunicorn --bind 0.0.0.0:${GUNICORN_PORT} --workers=${GUNICORN_WORKERS} --worker-class gevent composer.api.api:app"]