# How-To
- Generally, follow the K3s instructions... (https://docs.k3s.io/advanced#nvidia-container-runtime-support)

# Gotchas
- nvidia-container-runtime has to be set either as default or it needs to be present on every pod that wants to use the GPU (in `runtimeClassName`)

# Still ToDo / ToVerify
- Do we really need the fabricmanager, the K3s documentation mentions? Probably not...
- Is setting the nvidia container runtime as default the only option for avoiding `runtimeClassName: nvidia` on every pod? (is that even an issue?)

# Installation steps
- Install Nvidia driver (headless version)
- Install nvidia-container-toolkit
    ```sh
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
    && \
        sudo apt-get update && apt-get install -y nvidia-container-toolkit
    ```
- Install K3s (disable all components we do not need, and add tailscale name to api cert)
    ```sh
    curl -ksL get.k3s.io | INSTALL_K3S_EXEC="--disable traefik --disable servicelb --tls-san carmel-srv-vw-gpu" sh -
    ```
- Create runtimeClass "nvidia"
    ```sh
    kubectl apply -f nvidia.runtime-class.yaml
    ```
- Install nvidia-device-plugin (and enable CUDA time slicing)
    ```sh
    helm install nvdp nvdp/nvidia-device-plugin \
        --namespace nvidia-device-plugin --create-namespace \
        --version 0.14.1 -f nvidia-device-plugin.values.yaml
    ```
