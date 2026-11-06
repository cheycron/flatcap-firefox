# Disposable renderer for the Flatcap Firefox theme: real Firefox on Xvfb, driven by Selenium/geckodriver.
# Build:  docker build -t flatcap-ff-capture --build-arg FF_VERSION=159.0.1 scripts/capture
# Run:    see scripts/capture/capture.py (docs in README "Verifying")
FROM debian:bookworm-slim
ARG FF_VERSION=159.0.1
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl xz-utils bzip2 xvfb xdotool imagemagick x11-utils \
      python3 python3-pip python3-venv fonts-noto-core fonts-noto-color-emoji \
      libgtk-3-0 libdbus-glib-1-2 libasound2 libx11-xcb1 libxtst6 libxt6 libpci3 \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://ftp.mozilla.org/pub/firefox/releases/${FF_VERSION}/linux-x86_64/en-US/firefox-${FF_VERSION}.tar.xz" \
      | tar -xJ -C /opt \
    && ln -s /opt/firefox/firefox /usr/local/bin/firefox
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir selenium
RUN /opt/venv/bin/python - <<'PY'
# let Selenium Manager fetch geckodriver now, so the run needs no network
from selenium.webdriver.common.selenium_manager import SeleniumManager
print(SeleniumManager().binary_paths(["--browser", "firefox", "--browser-path", "/opt/firefox/firefox"]))
PY
COPY site /site
COPY capture.py /capture.py
ENTRYPOINT ["/opt/venv/bin/python", "/capture.py"]
