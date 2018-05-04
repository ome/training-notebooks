FROM imagedata/jupyter-docker:0.8.1
MAINTAINER ome-devel@lists.openmicroscopy.org.uk

# create a python2 environment (for OMERO-PY compatibility)
ADD docker/environment-python2-omero.yml .setup/
RUN conda env update -n python2 -f .setup/environment-python2-omero.yml

RUN /opt/conda/envs/python2/bin/python -m ipykernel install --user --name python2 --display-name 'OMERO Python 2'
ADD docker/logo-32x32.png docker/logo-64x64.png .local/share/jupyter/kernels/python2/

# Clone the source git repo into notebooks
# 20180418: COPY --chown doesn't work on Docker Hub
#COPY --chown=1000:100 . notebooks
COPY . notebooks
USER root
RUN chown -R 1000:100 notebooks
USER jovyan
