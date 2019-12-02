FROM imagedata/jupyter-docker:0.10.0
MAINTAINER ome-devel@lists.openmicroscopy.org.uk

# create a python2 environment (for OMERO-PY compatibility)
ADD docker/environment-python3-omero.yml .setup/
RUN conda env update -n python3 -q -f .setup/environment-python3-omero.yml
# Don't use this:
# /opt/conda/envs/python2/bin/python -m ipykernel install --user --name python3 --display-name 'OMERO Python 3'
# because it doesn't activate conda environment variables
COPY --chown=1000:100 docker/logo-32x32.png docker/logo-64x64.png .local/share/jupyter/kernels/python3/
COPY --chown=1000:100 docker/python3-kernel.json .local/share/jupyter/kernels/python3/kernel.json

# Cell Profiler (add to the Python3 environment)
# ADD docker/environment-python2-cellprofiler.yml .setup/
# RUN conda env update -n python3 -q -f .setup/environment-python2-cellprofiler.yml
# CellProfiler has to be installed in a separate step because it requires
# the JAVA_HOME environment variable set in the updated environment
# ARG CELLPROFILER_VERSION=v3.1.8
# RUN bash -c "source activate python3 && pip install git+https://github.com/CellProfiler/CellProfiler.git@$CELLPROFILER_VERSION"

# R-kernel and R-OMERO prerequisites
ADD docker/environment-r-omero.yml .setup/
RUN conda env update -n r-omero -q -f .setup/environment-r-omero.yml && \
    /opt/conda/envs/r-omero/bin/Rscript -e "IRkernel::installspec(displayname='OMERO R')"

# Install BeakerX
# Necessary to instal in a separate command
RUN conda install -c anaconda numpy
RUN conda install -c conda-forge beakerx && \
    # Jupyterlab component for ipywidgets (must match jupyterlab version) \
    jupyter labextension install beakerx-jupyterlab

USER root
RUN mkdir /opt/romero /opt/omero /opt/java-apps /opt/python-apps && \
    fix-permissions /opt/romero /opt/omero /opt/java-apps /opt/python-apps
# R requires these two packages at runtime
RUN apt-get install -y -q \
    libxrender1 \
    libsm6

RUN apt-get install -y -q \
    unzip

RUN apt-get update && apt-get install -y -q \
    --no-install-recommends bsdtar

# Install FIJI and few plugins
RUN cd /opt/java-apps && \
    wget -q https://downloads.imagej.net/fiji/latest/fiji-linux64.zip && \
    unzip fiji-linux64.zip
RUN cd /opt/java-apps/Fiji.app/plugins && \
    wget -q https://github.com/ome/omero-insight/releases/download/v5.5.6/OMERO.imagej-5.5.6.zip && \
    unzip OMERO.imagej-5.5.6.zip && rm OMERO.imagej-5.5.6.zip

RUN /opt/java-apps/Fiji.app/ImageJ-linux64 --update add-update-site BF https://sites.imagej.net/Bio-Formats/

# Install Orbit
RUN cd /opt/java-apps && \
    curl -s http://www.stritt.de/files/orbit_linux_315.tar.gz | tar xz

# Install ilastik
ARG ILASTIK_VERSION=ilastik-1.3.2post1-Linux.tar.bz2
ADD http://files.ilastik.org/$ILASTIK_VERSION /opt/python-apps/
RUN cd /opt/python-apps && mkdir ilastik-release && \
    bsdtar xjf /opt/python-apps/$ILASTIK_VERSION -C /opt/python-apps/ilastik-release --strip-components=1 && rm /opt/python-apps/$ILASTIK_VERSION

RUN apt-get update && \
    apt-get install -y \
        apt-utils \
        software-properties-common && \
    apt-get upgrade -y
 
# get Xvfb virtual X server and configure
RUN apt-get install -y \
        xvfb \
        x11vnc \
        x11-xkb-utils \
        xfonts-100dpi \
        xfonts-75dpi \
        xfonts-scalable \
        xfonts-cyrillic \
        x11-apps \
        libxrender1 \
        libxtst6 \
        libxi6 
                    
# Setting ENV for Xvfb and Fiji
ENV DISPLAY :99
ENV PATH $PATH:/opt/java-apps/Fiji.app/

# Adjust start.sh
#RUN sed -i 's/exec \$cmd/exec xvfb-run \$cmd/' /usr/local/bin/start.sh
RUN sed -i 's/exec/exec xvfb-run/' /usr/local/bin/start.sh

USER $NB_UID

# install rOMERO
ENV _JAVA_OPTIONS="-Xss2560k -Xmx2g"
ENV OMERO_LIBS_DOWNLOAD=TRUE
ARG ROMERO_VERSION=v0.4.7
RUN cd /opt/romero && \
    curl -sf https://raw.githubusercontent.com/ome/rOMERO-gateway/$ROMERO_VERSION/install.R --output install.R && \
    bash -c "source activate r-omero && Rscript install.R --version=$ROMERO_VERSION --quiet"

# OMERO full CLI
# This currently uses the python2 environment, should we move it to its own?
ARG OMERO_VERSION=5.5.0
RUN cd /opt/omero && \
    /opt/conda/envs/python3/bin/pip install -q omego && \
    /opt/conda/envs/python3/bin/omego download -q --sym OMERO.server server --release $OMERO_VERSION && \
    rm OMERO.server-*.zip
ADD docker/omero-bin.sh /usr/local/bin/omero

# Clone the source git repo into notebooks (keep this at the end of the file)
COPY --chown=1000:100 . notebooks
