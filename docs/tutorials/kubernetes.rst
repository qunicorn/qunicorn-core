Run using kubernetes / minikube
=========================================

Installation / Starting Minikube (tested for windows)
----------------------

1. Install `Chocolatey <https://chocolatey.org/install#individual>`_

2. Install Minikube `Minikube <https://minikube.sigs.k8s.io/docs/>`_

.. code-block:: bash

    choco install minikube

3. Install kubectl `kubectl <https://kubernetes.io/docs/setup/>`_

.. code-block:: bash

    choco install kubernetes-cli

4. Install kubernetes-kompose

.. code-block:: bash

    choco install kubernetes-kompose

5. Navigate to the location where the docker-compose file is. It should be under 'C:\...\qunicorn-core'.
6. Now check if a minikube folder has been created under 'C:\...\qunicorn-core'.
   If not, create the kubernetes configuration files.
   This will generate a folder called minikube with all the kubernetes configuration files based on the docker-compose.
   However this might overwrite custom changes made to the files, if already existing. Proceed with caution.

.. code-block:: bash

    kompose convert -f docker-compose.yaml --out minikube

7. Start Docker (e.g. Docker Desktop)
8. Start minikube

.. code-block:: bash

    minikube start

9. Set minikube as docker env

   Minikube needs to be set as docker environment to be able to build images for minikube. Otherwise Minikube would not be able to find the images. This needs to be done every time a new terminal is opened.

.. code-block:: bash

    minikube docker-env | Invoke-Expression
    
You can also load local images into Minikube with

.. code-block:: bash

    minikube image load {image-name}

10. Build qunicorn image

.. code-block:: bash

    docker build -t qunicorn:local .

11. Start services and pods with configuration (Note that starting the whole cluster can take a while (up or more than 8min))

.. code-block:: bash

    kubectl apply -f minikube

12. Expose qunicorn through minikube (start in another terminal)
    Exposes the qunicorn service to the internet. This is needed to be able to access the service from outside the cluster.

.. code-block:: bash

    minikube tunnel

Alternatively, you can access the qunicorn service with the following command.

.. code-block:: bash

    minikube service qunicorn

13. List service information using

.. code-block:: bash

    kubectl get svc

14. Get existing pos and fill database with data

.. code-block:: bash

    kubectl get po --selector=io.kompose.service=server

15. Now you can access qunicorn using [EXTERNAL-IP]:8080/swagger-ui of the server service (usually you can use localhost)



Other useful commands
----------------------

* Clear all kubectl pods and services

.. code-block:: bash

    kubectl delete daemonsets,replicasets,services,deployments,pods,rc,ingress --all --all-namespaces

* Expose service and create Tunnel

.. code-block:: bash

    minikube service {service}

* Visual dashboard to view cluster information

.. code-block:: bash

    minikube dashboard



================================================================

A tutorial on how to deploy the helm charts
=====================

helm installation
#################

[Helm](https://helm.sh) must be installed to use the charts.  Please refer to Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, then we need:

1. To install the <chart-name> chart:

    :code:`cd <helm-chart-folder>`

    :code:`helm install <my-chart-name> .`

2. To uninstall the chart:

    :code:`helm delete <my-chart-name>`


Converting YAML files into helm charts
##############################

Using helmify


1. Step1 . Installation of helmify

   (https://formulae.brew.sh/formula/helmify)

2. Step2 . Convert YAML files to Helm chart

    a . For single yaml file: 
        
        :code:`cat <your-yamlfile-name>.yaml | helmify <chart-name>`

    b . From directory with yamls: 
        
        :code:`awk 'FNR==1 && NR!=1  {print "---"}{print}' /<my_directory>/*.yaml | helmify <helmchart-folder-name>`