FROM imagedata/jupyter-docker:0.9.0
MAINTAINER ome-devel@lists.openmicroscopy.org.uk

# create a python2 environment (for OMERO-PY compatibility)
ADD docker/environment-python2-omero.yml .setup/
RUN conda env update -n python2 -q -f .setup/environment-python2-omero.yml
# Don't use this:
# /opt/conda/envs/python2/bin/python -m ipykernel install --user --name python2 --display-name 'OMERO Python 2'
# because it doesn't activate conda environment variables
COPY --chown=1000:100 docker/logo-32x32.png docker/logo-64x64.png .local/share/jupyter/kernels/python2/
COPY --chown=1000:100 docker/python2-kernel.json .local/share/jupyter/kernels/python2/kernel.json

# Cell Profiler (add to the Python2 environment)
ADD docker/environment-python2-cellprofiler.yml .setup/
RUN conda env update -n python2 -q -f .setup/environment-python2-cellprofiler.yml
# CellProfiler has to be installed in a separate step because it requires
# the JAVA_HOME environment variable set in the updated environment
ARG CELLPROFILER_VERSION=v3.1.3
RUN bash -c "source activate python2 && pip install git+https://github.com/CellProfiler/CellProfiler.git@$CELLPROFILER_VERSION"

# R-kernel and R-OMERO prerequisites
ADD docker/environment-r-omero.yml .setup/
RUN conda env update -n r-omero -q -f .setup/environment-r-omero.yml && \
    /opt/conda/envs/r-omero/bin/Rscript -e "IRkernel::installspec(displayname='OMERO R')"

USER root
RUN mkdir /opt/romero /opt/omero && \
    fix-permissions /opt/romero /opt/omero
# R requires these two packages at runtime
RUN apt-get install -y -q \
    libxrender1 \
    libsm6
USER $NB_UID

# install rOMERO
ENV _JAVA_OPTIONS="-Xss2560k -Xmx2g"
ARG ROMERO_VERSION=v0.4.3
RUN cd /opt/romero && \
    curl -sf https://raw.githubusercontent.com/ome/rOMERO-gateway/$ROMERO_VERSION/install.R --output install.R && \
    bash -c "source activate r-omero && Rscript install.R --version=$ROMERO_VERSION --quiet"

# OMERO full CLI
# This currently uses the python2 environment, should we move it to its own?
ARG OMERO_VERSION=5.4.9
RUN cd /opt/omero && \
    /opt/conda/envs/python2/bin/pip install -q omego && \
    /opt/conda/envs/python2/bin/omego download -q --sym OMERO.server server --release $OMERO_VERSION && \
    rm OMERO.server-*.zip
ADD docker/omero-bin.sh /usr/local/bin/omero

# Clone the source git repo into notebooks (keep this at the end of the file)
COPY --chown=1000:100 . notebooks
