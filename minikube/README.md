## Minikube Deployment

To start the deployment, the broker and server need secrets.
These can be created with the following commands:

On linux:

```bash
kubectl create secret generic broker-secret --from-literal=password='brokerpassword'
kubectl create secret generic qmware-secret --from-literal=QMWARE_API_KEY='apikeyhere' --from-literal=QMWARE_API_KEY_ID='apikeyidhere'
```

For local testing the provided dummy values above suffice.

To start the deployment with minikube, start minikube and apply the deployment.

```bash
cd minikube
minikube start
kubectl apply -f .
```

The API is available via the minikube services, e.g.:

```bash
minikube service server
```
