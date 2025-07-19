# Matachana Simulator

A lightweight Python-based simulator for Matachana IoT devices, designed for testing and development environments. This container mimics device behavior over HTTP and is ideal for integration validation, load testing, or developing against virtual Matachana endpoints.

## 🐳 Usage with Docker Compose

To spin up multiple simulated devices, you can use the following `docker-compose.yml` example. Each instance listens on the same ports (8000/8001), but binds to a **different virtual IP address** on the host system:

```yaml
services:
  sim1:
    image: matachana-simulator
    container_name: matachana-sim-1
    ports:
      - "192.168.1.90:8000:8000"
      - "192.168.1.90:8001:8001"

  sim2:
    image: matachana-simulator
    container_name: matachana-sim-2
    ports:
      - "192.168.1.91:8000:8000"
      - "192.168.1.91:8001:8001"

  sim3:
    image: matachana-simulator
    container_name: matachana-sim-3
    ports:
      - "192.168.1.92:8000:8000"
      - "192.168.1.92:8001:8001"

  sim4:
    image: matachana-simulator
    container_name: matachana-sim-4
    ports:
      - "192.168.1.93:8000:8000"
      - "192.168.1.93:8001:8001"

  sim5:
    image: matachana-simulator
    container_name: matachana-sim-5
    ports:
      - "192.168.1.94:8000:8000"
      - "192.168.1.94:8001:8001"


Recommended: Use Virtual IP Addresses
Running multiple containers that expose the same ports (e.g. 8000, 8001) on a single host requires using virtual IPs to avoid port conflicts.

🧪 Example Linux Commands to Add Virtual IPs
Run these on your Linux host (replace enp37s0 with your actual NIC if different):
sudo ip addr add 192.168.1.90/24 dev enp37s0 label enp37s0:1
sudo ip addr add 192.168.1.91/24 dev enp37s0 label enp37s0:2
sudo ip addr add 192.168.1.92/24 dev enp37s0 label enp37s0:3
sudo ip addr add 192.168.1.93/24 dev enp37s0 label enp37s0:4
sudo ip addr add 192.168.1.94/24 dev enp37s0 label enp37s0:5


🔄 To Make Virtual IPs Persistent (Optional)
To keep them after reboot, you'll need to configure them via:

netplan (Ubuntu 18.04+)

or /etc/network/interfaces (legacy systems)


📦 Pull the Image
docker pull marcojmarinelli/matachana-simulator

🚀 Run Manually
docker run -d \
  -p 8000:8000 \
  -p 8001:8001 \
  --name matachana-sim \
  marcojmarinelli/matachana-simulator


🤝 Contributing
Feel free to fork this repo and suggest improvements or open issues!
