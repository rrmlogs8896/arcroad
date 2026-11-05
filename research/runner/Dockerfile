# arcroad research runner (Cloudflare Containers). Built by wrangler on the iMac (needs Docker running).
FROM python:3.12-slim
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends osmium-tool git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "osmium>=3.6" "numpy>=1.24" "pandas>=2.0" "scipy>=1.11" "tabulate>=0.9" "rasterio>=1.3" "shapely>=2.0"
WORKDIR /app
COPY app/ /app/
EXPOSE 8080
CMD ["python", "server.py"]
