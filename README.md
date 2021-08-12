# K8S Intro

This is a basic walk-through over some basic k8s concepts as well as some tools commonly used to
deploy apps.

Before starting we need to install these tools:

* [docker](https://docs.docker.com/get-docker/)
* [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
* [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
* [helm](https://helm.sh/docs/intro/install/)

## Setup

To be able to play around we need to spin up a local k8s cluster. We'll use
[kind](https://kind.sigs.k8s.io/) to create the cluster and
[ingress-nginx](https://kubernetes.github.io/ingress-nginx/) as an ingress-controller to be able to
access our app from outside the cluster.
This setup was taken from the [kind page](https://kind.sigs.k8s.io/docs/user/ingress/),
so kudos to them :)

### Cluster

Let's start creating the cluster by running

```bash
kind create cluster --config assets/kind-config.yaml
```

This command will create a three-node cluster with one control-plane node and two workers.

### Ingress-controller

Once the cluster is up and running the next step is to be able to access our apps from outside. The
ingress-controller will do the work, we just need to run

```bash
kubectl apply -f assets/ingress-controller.yaml
```

This command will create all the necessary resources to handle external requests and forward them to
the proper service.

### Exposing our app

So the ingress-controller will route the traffic, but we need to tell it where to route it. How an
ingress work is beyond the scope of this guide. We'll just run this command

```bash
kubectl apply -f k8s/ingress.yaml
```

## Building our app

We'll build a really simple python app with 3 endpoints:

* `/whoami`: Will return the hostname the app is running in
* `/fail`: Will make our app fail (exit with status 1)
* `/db`: Will connect to a MySQL DB and show its version

Here we took advantage of [GitHub Actions](https://github.com/features/actions) to automatically
build and push our app to Dockerhub on any change to the Dockerfile or the app code in the main
branch.

If you want to build your image locally please run this command

```bash
docker build . -t k8s-app
```

## Configuring our app

To decouple your app from any environment-specific config it's a
[best practice](https://12factor.net/config) to store these configs in the environment itself
and not in the app. Kubernetes offers two options for this.

### ConfigMap

As the name says, is a key-value map in which you can store variables or files. Kubernetes saves
this object in plain text. We'll store our DB host and port in a ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### Secret

Secrets are similar to [ConfigMaps](#ConfigMap) but are specifically intended to hold confidential
data. Kubernetes offers different
[secret types](https://kubernetes.io/docs/concepts/configuration/secret/#secret-types) to store
different kinds of information. We'll store our DB credentials in a secret.

```bash
kubectl apply -f k8s/secret.yaml
```

> :warning: **WARNING**: These objects are stored base 64 encoded in the Kubernetes DB but this
feature itself doesn't provide any kind of secrecy nor encryption.

## Running our app

After our app is built and we have all the required configs we need to run it somewhere. Let's go
through different ways of doing so and see the benefits of using a container orchestrator.

### Single container outside k8s

First of all, let's run our app as a standalone container using docker.

```bash
docker run -d -p 5000:5000 lucasgiaco91/k8s-app
```

Our app is up and running and that's awesome! If you curl it at `localhost:5000/whoami` you'll get
the container ID.

As we know if anything could go wrong it will go wrong. So, let's curl at `localhost:5000/fail` and
see that the container ends unexpectedly. If this happens in a productive environment our app will
offline until we manually restart it.

It would be great if someone or something automatically restarts our container any time it fails
right? Here is where k8s comes in.

### Standalone pod

The minimum execution unit in k8s is a
[pod](https://kubernetes.io/docs/concepts/workloads/pods/). A pod is a group of one or more
containers that runs simultaneously. Let's run our container inside a pod and see how it comes.

```bash
kubectl apply -f k8s/pod.yaml
```

It's important to notice the `restartPolicy: Always` line in the pod declaration. This line will
tell k8s to restart our container any time it's not running.

Now if we curl our app at `localhost/fail` as we did in the previous section we'll see that our app
still fails but this time it's being automatically restarted every time.

```bash
❯ kubectl get po
NAME                       READY   STATUS    RESTARTS   AGE
k8s-app                    1/1     Running   1          2m52s
```

This is a great improvement!

If we want to avoid having a single point of failure, we'll need to manage several copies of our app
at the same time, ensuring that all of them are running the same app version and that all of them
are configured in the same way. Let's look at what k8s has to offer to tackle this issue.

### Deployment

A [deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) is a
desired state description of our app that declares how our pods are configured and how many
instances of them we want. Kubernetes will watch this config and will ensure that all our app's
replicas are always running. If anyone fails for whatever reason, it will be replaced.

Let's deploy our app inside a deployment now.

```bash
kubectl apply -f k8s/deployment.yaml
```

Now that our 3 replicas are running, we need to be able to route traffic to all of them. A
[service](https://kubernetes.io/docs/concepts/services-networking/service/) is an abstract object
that groups pods and routes traffic to them. This target group is defined by a selector using
[labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/).

As we already labeled our pods with `app: k8s-app`, let's configure a service to use that label.

```bash
kubectl apply -f k8s/svc.yaml
```

To prove that the service is working let's curl at `localhost/whoami` several times and we'll get
different pod names in each request.

## External dependencies

In this last step, we want to connect our app to a database. Curling at `localhost/db` will show
that is not able to connect to the DB as there's no DB at all!

One widely used tool to deploy apps in k8s is [helm](https://helm.sh/). Think of helm as a package
manager for k8s that will help us to install a MySQL in our cluster.

Let's install it, and while we wait let's dig into some helm concepts.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install mysql bitnami/mysql --set auth.rootPassword=R00t! --namespace db --create-namespace --wait
```

The first two commands tell helm the chat's location (repo) and grab all the information about
the charts stored there. The last one is the one installing the chart with some flags that are worth
noticing:

* `--namespace`: This flag tells helm in which namespace the chart will be installed
* `--create-namespace`: This flag tells helm to create the namespace if it doesn't exist
* `--wait`: This flag tells helm to hold the prompt until all pods are ready
* `--set`: This flag provides a value to overwrite from the chart's default. We're setting the MySQL
root password
* `bitnami/mysql`: This is the chart location. We want to install the chart mysql from bitnami's
repo
* `mysql`: This is the chart name. It must be unique inside a namespace

Now that our chart is installed, if we curl at `localhost/db` our app will be able to connect to the
DB and retrieve its version.

If you want to try to install any other chart, I would recommend looking for it at
[artifact-hub](https://artifacthub.io/)

## Teardown

Once you're done playing with the local cluster just run this command to delete the cluster

```bash
kind delete cluster --name local
```
