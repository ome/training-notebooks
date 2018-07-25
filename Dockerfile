FROM imagedata/jupyter-docker:0.8.1
MAINTAINER ome-devel@lists.openmicroscopy.org.uk

# create a python2 environment (for OMERO-PY compatibility)
ADD docker/environment-python2-omero.yml .setup/
RUN conda env update -n python2 -f .setup/environment-python2-omero.yml
# Don't use this:
# /opt/conda/envs/python2/bin/python -m ipykernel install --user --name python2 --display-name 'OMERO Python 2'
# because it doesn't activate conda environment variables
ADD docker/logo-32x32.png docker/logo-64x64.png .local/share/jupyter/kernels/python2/
ADD docker/python2-kernel.json .local/share/jupyter/kernels/python2/kernel.json
USER root
RUN fix-permissions .local
USER $NB_UID

# Cell Profiler (add to the Python2 environment)
ADD docker/environment-python2-cellprofiler.yml .setup/
RUN conda env update -n python2 -f .setup/environment-python2-cellprofiler.yml
# CellProfiler has to be installed in a separate step because it requires
# the JAVA_HOME environment variable set in the updated environment
ARG CELLPROFILER_VERSION=v3.1.3
RUN bash -c "source activate python2 && pip install git+https://github.com/CellProfiler/CellProfiler.git@$CELLPROFILER_VERSION"

# Install prerequisites to install R
RUN apt-get update && \
    apt-get -y install libssl-dev \
    libxml2-dev \
    libcurl4-openssl-dev \
    libpcre3 \
    libpcre3-dev \
    liblzma-dev \
    libbz2-dev \
    libjpeg-dev \
    libssh2-1-dev \
    libtiff-dev \
    libpng-dev \
    libfftw3-dev

# Install newer version of R. Run apt-get -y install r-base installs version 3.2
RUN sudo echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" | sudo tee -a /etc/apt/sources.list
RUN gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9
RUN gpg -a --export E084DAB9 | sudo apt-key add -
RUN apt-get update
RUN apt-get install -y --no-install-recommends r-recommended r-base


RUN R CMD javareconf

# Required for romero
RUN apt-get install -y git maven \ 
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


## make sure Java can be found in rApache and other daemons not looking in R ldpaths
RUN echo "/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64/server/" > /etc/ld.so.conf.d/rJava.conf
RUN /sbin/ldconfig
RUN rm -rf /usr/lib/jvm/java
RUN ln -s  /usr/lib/jvm/java-8-openjdk-amd64 /usr/lib/jvm/java


## Install rJava package
RUN apt-get update \
    && apt-get install -y r-cran-rjava

# Change owner
RUN chown jovyan /usr/local/lib/R/site-library

RUN mkdir /romero \
 && curl https://raw.githubusercontent.com/dominikl/rOMERO-gateway/63906f92fcd7458738a342ebae9c0f9f177416dc/install.R --output install.R


# install rOMERO
ENV _JAVA_OPTIONS="-Xss2560k -Xmx2g"

RUN Rscript install.R --version=v0.4.0

# install r-kernel and make it accessible
RUN Rscript -e "install.packages(c(\"devtools\"), repos = c(\"http://irkernel.github.io/\", \"http://cran.rstudio.com\"))"

RUN Rscript -e "library(\"devtools\")" \
-e "install_github(\"IRkernel/repr\")" \
-e "install_github(\"IRkernel/IRdisplay\")" \
-e "install_github('IRkernel/IRkernel')" \
-e "IRkernel::installspec()" \
-e "install.packages(\"tidyverse\")" \
-e "source(\"https://bioconductor.org/biocLite.R\")" \
-e "biocLite(\"EBImage\")"

# Delete the installation file
RUN rm install.R

ARG OMERO_SERVER=OMERO.server-5.4.6-ice36-b87
RUN mkdir /opt/omero && \
    cd /opt/omero && \
    wget -q http://downloads.openmicroscopy.org/omero/5.4.6/artifacts/${OMERO_SERVER}.zip && \
    unzip -q ${OMERO_SERVER}.zip && \
    rm ${OMERO_SERVER}.zip && \
    ln -s ${OMERO_SERVER} OMERO.server && \
    echo '#!/bin/sh\nexec /opt/conda/envs/python2/bin/python /opt/omero/OMERO.server/bin/omero "$@"' > /usr/local/bin/omero && \
    chmod 755 /usr/local/bin/omero

# Clone the source git repo into notebooks
# 20180418: COPY --chown doesn't work on Docker Hub
#COPY --chown=1000:100 . notebooks
COPY . notebooks
RUN chown -R 1000:100 notebooks
USER jovyan
