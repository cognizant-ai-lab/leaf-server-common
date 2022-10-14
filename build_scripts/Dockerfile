# Base image
FROM python:3.8-slim

##############################################################
#			Basic Housekeeping
##############################################################
LABEL maintainer=donn.goodhew@cognizant.com
ENV LANG C.UTF-8
ENV ESP_PYTHON_VERSION 3.8
ENV PIP3_VERSION 22.2.2
ENV DEBIAN_FRONTEND noninteractive

# Debian basics
RUN apt-get update -y
RUN apt-get install curl -y

# Last vestige of ENN_SOURCE_CREDENTIALS
ENV LEAF_SOURCE_CREDENTIALS=${ENN_SOURCE_CREDENTIALS}
RUN  adduser --disabled-password --gecos '' leaf
# The app home is our root directory within the image
# where we place the repo's source directory.
# We place the required private repo source directories
# inside the repo directory. The private repo shuffling
# is handled by Codefresh using our private-dependency plugin.
ENV REPO leaf-server-common
ENV APP_HOME /home/leaf
ENV APP_SOURCE ${APP_HOME}/${REPO}
# ENV ESP_SDK_RELATIVE ${REPO}/esp-sdk
# ENV ESP_SDK_HOME ${APP_HOME}/${ESP_SDK_RELATIVE}
USER leaf
ENV our_venv ${APP_HOME}/venv/esp-${ESP_PYTHON_VERSION}
ENV PATH="$our_venv/bin:$PATH"

# Make directories as needed
RUN mkdir -p ${APP_HOME}
             # ${ESP_SDK_HOME}

# Set up python and pip
RUN python${ESP_PYTHON_VERSION} -m venv $our_venv
RUN pip3 install --upgrade pip==${PIP3_VERSION} \
    && pip3 install wheel \
                    virtualenv

# Copy and install our private dependencies as individual layers
# to maximize cache hits and minimize build time.

# Start with esp-sdk which changes at its own pace and
# relatively infrequently.
# COPY --chown=leaf:leaf ${ESP_SDK_RELATIVE}/requirements.txt ${ESP_SDK_HOME}
# RUN /bin/bash -c "pip3 install -r <(sed '/git+https/d' ${ESP_SDK_HOME}/requirements.txt)"

# Now bring all of our requirement files in
# and pip install as needed. These requirements change at their own pace
# and more frequently than esp-sdk and completion-service which we installed above.
# Create a separate layer for each of the requirements files for maximum
# caching performance. Ordered by general frequency of change, least-to-most.
COPY --chown=leaf:leaf ${REPO}/requirements-build.txt ${APP_SOURCE}
RUN /bin/bash -c "pip3 install -r <(sed '/git+https/d' ${APP_SOURCE}/requirements-build.txt)"

COPY --chown=leaf:leaf  ${REPO}/requirements.txt ${APP_SOURCE}
RUN /bin/bash -c "pip3 install -r <(sed '/git+https/d' ${APP_SOURCE}/requirements.txt)"

# leaf-common has no dependencies, so there is no pip install for that

# Now we copy the full source tree into the container, which will almost always
# in practice break the cache since we build when code changes.
COPY --chown=leaf:leaf . ${APP_HOME}

ENV PYTHONPATH="${PYTHONPATH}:${APP_SOURCE}/leaf-common"
WORKDIR ${APP_HOME}
