FROM node:22-bookworm-slim
ARG OPENCODE_VERSION=1.18.31
RUN npm install --global opencode-ai@${OPENCODE_VERSION}
WORKDIR /workspace
COPY opencode.json /workspace/opencode.json
ENV OPENCODE_DISABLE_AUTOUPDATE=1 OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_CONFIG=/workspace/opencode.json
ENV XDG_CONFIG_HOME=/runtime/config XDG_DATA_HOME=/runtime/data XDG_CACHE_HOME=/runtime/cache
EXPOSE 4096
CMD ["opencode", "serve", "--pure", "--hostname", "0.0.0.0", "--port", "4096"]
