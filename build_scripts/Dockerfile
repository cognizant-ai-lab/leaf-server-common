# Base image
FROM python:3.8-slim

##############################################################
#			Basic Housekeeping
##############################################################
LABEL maintainer=donn.goodhew@cognizant.com
ENV LANG C.UTF-8
ENV PYTHON_VERSION 3.8
ENV PIP3_VERSION 22.3
ENV DEBIAN_FRONTEND noninteractive
ENV USERNAME leaf

# Debian basics
RUN apt-get update -y
RUN apt-get install curl git -y

RUN  adduser --disabled-password --gecos '' ${USERNAME}

# Change EXTERNAL_BUILD_ROOT to . if debugging locally
ENV EXTERNAL_BUILD_ROOT .

# The APP_HOME home is our root directory within the image
# where we place the repo's source directory.
ENV APP_HOME /home/${USERNAME}

ENV OUR_VENV ${APP_HOME}/venv/python-${PYTHON_VERSION}
ENV PATH="$OUR_VENV/bin:$PATH"

# Make directories as needed
RUN mkdir -p ${APP_HOME}

# Set up python and pip
RUN python${PYTHON_VERSION} -m venv $OUR_VENV
RUN pip3 install --upgrade pip==${PIP3_VERSION} \
    && pip3 install wheel \
                    virtualenv

# This container expects the name of the REPO passed in as a build argument
ARG REPO
ENV APP_SOURCE ${APP_HOME}/${REPO}
RUN mkdir -p ${APP_SOURCE}

# Now bring all of our requirement files in and pip install as needed.
# Create a separate layer for each of the requirements files for maximum
# caching performance. Ordered by general frequency of change, least-to-most.
# We use A COPY step before the pip install in the RUN step so that requirements
# only changes cause a proper container rebuild.
COPY --chown=${USERNAME}:${USERNAME} ${EXTERNAL_BUILD_ROOT}/requirements-build.txt ${APP_SOURCE}
RUN /bin/bash -c "pip3 install -r ${APP_SOURCE}/requirements-build.txt"

# Use the with_creds_requirements secret as the basis for the pip install
# of the main requirements.  We still do the COPY first so the container
# cache is properly broken on changes.
#
# NOTE: We expect the with_creds_requirement file to provide us with
#       ephemeral GitHub creds from vault as the proper replacement mechanism
#       for LEAF_SOURCE_CREDENTIALS.  This way, it's OK if these inherently
#       short-lived happen to be stored in the container.
COPY --chown=${USERNAME}:${USERNAME}  ${EXTERNAL_BUILD_ROOT}/requirements.txt ${APP_SOURCE}
RUN --mount=type=secret,id=with_creds_requirements \
    /bin/bash -c "pip3 install -r <(cat /run/secrets/with_creds_requirements)"

# Now we copy the full source tree into the container, which will almost always
# in practice break the cache since we build when code changes.
USER ${USERNAME}
COPY --chown=${USERNAME}:${USERNAME} . ${APP_HOME}

WORKDIR ${APP_HOME}
