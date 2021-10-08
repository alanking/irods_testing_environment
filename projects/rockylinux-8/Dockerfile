FROM rockylinux/rockylinux:8

RUN yum update -y && \
    yum install -y \
        rocky-release \
        wget \
        python3 \
        python3-psutil \
        python3-requests \
        python3-jsonschema \
        python3-pip \
        rsyslog \
        gnupg \
        unixODBC-devel \
        authd

RUN rpm --import https://packages.irods.org/irods-signing-key.asc && \
    wget -qO - https://packages.irods.org/renci-irods.yum.repo | tee /etc/yum.repos.d/renci-irods.yum.repo && \
    yum update -y

ENTRYPOINT ["bash", "-c", "until false; do sleep 2147483647d; done"]
