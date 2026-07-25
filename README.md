# 🚀 Flask App Deployment on Kubernetes using Helm (Beginner Friendly Guide)

Ye project sikhata hai ke ek **Flask app** ko **Docker + Kubernetes + Helm** ke through kaise deploy karte hain — bilkul asaan alfaz mein, jesay ek naya bunda (beginner) bhi samajh sakay. 😊

---

## 📌 Ye Project Kya Karta Hai?

Simple lafzon mein:
1. Hum ek **Flask app** (chota web application) banate hain.
2. Usay **Docker** mein pack karte hain (jese saman ko dabbe mein pack karna).
3. Phir **Kubernetes** (K8s) pe chalate hain — jo dabbon ko manage/organize karta hai.
4. **Helm** ka use karte hain taake deployment easy aur repeatable ho — jese ek "install button" jo sara setup automatically kar de.

---

## 🧠 Kuch Basic Cheezain Samjhein (Simple Words Mein)

| Term | Simple Matlab |
|---|---|
| **Docker** | App ko ek dabbe (container) mein band karna, taake wo kisi bhi machine pe chal sakay |
| **Kubernetes (K8s)** | Bohat saare containers ko organize aur manage karne wala system |
| **Helm** | Kubernetes ka "installer" — ek command se poora app deploy ho jata hai |
| **Helm Chart** | Ek folder jisme app ke saare settings (YAML files) hoti hain |
| **KIND** | Apne laptop/server pe chota Kubernetes cluster banane ka tool (testing ke liye) |
| **EKS** | AWS ka managed Kubernetes (real/production use ke liye) |

---

## 🏗️ Project Ka Design (Architecture)

```
Developer → Helm Chart → Helm CLI → Kubernetes Cluster → Pod → Service → Ingress → User
```

Yani: Developer code likhta hai → Helm us code ko Kubernetes tak deploy karta hai → App end mein user tak pohanch jata hai. ✅

---

## 📂 Project Structure

```
flask-stack/
├── Chart.yaml              # Main chart ki info
├── values.yaml              # Settings (config)
├── charts/
│   ├── flask-app/           # Flask backend
│   └── nginx-proxy/         # NGINX proxy (traffic manage karne wala)
```

Hum **Umbrella Chart approach** use karte hain — matlab ek "parent" chart do "child" charts (flask-app + nginx-proxy) ko control karta hai. Bade companies jese Netflix aur AWS bhi ye approach use karti hain.

---

## ⚙️ Step-by-Step Setup

### 1️⃣ EC2 Server Banayen (AWS)
- Ubuntu 22.04, t2.medium instance
- Ports open karein: 22, 80, 443, 6443, 8080

```bash
ssh -i "your-key.pem" ubuntu@<EC2_PUBLIC_IP>
```

### 2️⃣ Docker Install Karein
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

### 3️⃣ Kubectl aur KIND Install Karein
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/kubectl

curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### 4️⃣ Local Kubernetes Cluster Banayen (KIND)
```bash
kind create cluster --name helm --config=kind-config.yaml
kubectl cluster-info
kubectl get nodes
```

### 5️⃣ Helm Install Karein
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

### 6️⃣ Helm Chart Banayen aur Deploy Karein
```bash
helm create flask-stack
cd flask-stack
helm install flask-stack .
```

✅ Ye command Flask app aur NGINX dono ko ek sath deploy kar degi.

---

## 🔄 Update / Rollback / Remove Karna

```bash
helm upgrade flask-stack .     # Naye changes deploy karne ke liye
helm status flask-stack        # Status dekhne ke liye
helm rollback flask-stack 1    # Purani version pe wapas jane ke liye
helm uninstall flask-stack     # Sab hata dene ke liye
```

---

## 🌐 Helm Chart Ko GitHub Pe Host Karna

```bash
helm package flask-stack/
helm repo index . --url https://<username>.github.io/helm-charts
git add .
git commit -m "Add flask-stack chart"
git push
```

Phir GitHub Settings → Pages se enable kar dein. Bas! Ab aapka Helm chart online available hai. 🎉

---

## 💼 Ye Approach Kyun Best Hai?

| Faida | Matlab |
|---|---|
| 🧱 Modularity | Har service (Flask, NGINX) ko alag se update/scale kar sakte hain |
| 🚀 CI/CD Ready | Automatic pipelines ke sath easily chalta hai |
| 🔄 Easy Rollback | Kisi bhi purani version pe fori wapas ja sakte hain |
| ☁️ Cloud Agnostic | EKS, GKE, AKS — har jagah kaam karta hai |

---

## ✅ Conclusion

Ye project sikhata hai ke ek complete **DevOps pipeline** kaise banti hai:
> AWS Server → Docker → Kubernetes → Helm → Live App 🚀

Ye wahi tareeqa hai jo real companies (Netflix, Spotify, aur startups) use karti hain apne apps deploy karne ke liye.

---

### 🔗 Useful Links
- [Helm Official Docs](https://helm.sh/docs/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [KIND Docs](https://kind.sigs.k8s.io/)
