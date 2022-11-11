FROM python:3.10.6-buster

RUN mkdir /opt/stable-diffusion
WORKDIR /opt/stable-diffusion

COPY setup-00-base.sh /opt/stable-diffusion/
RUN chmod +x setup-00-base.sh && ./setup-00-base.sh

COPY setup-01-pip.sh /opt/stable-diffusion/
RUN chmod +x setup-01-pip.sh && ./setup-01-pip.sh

COPY setup-02-repos.sh /opt/stable-diffusion/
RUN chmod +x setup-02-repos.sh && ./setup-02-repos.sh

COPY setup-03-reqs.sh /opt/stable-diffusion/
RUN chmod +x setup-03-reqs.sh && ./setup-03-reqs.sh

RUN apt update && apt install -y ffmpeg libsm6 libxext6

COPY setup-04-models.sh /opt/stable-diffusion/
RUN chmod +x setup-04-models.sh && ./setup-04-models.sh

COPY webui.sh /opt/stable-diffusion/
ENTRYPOINT ["/opt/stable-diffusion/webui.sh"]
