# Introduction

This guide is to help you develop NVFLARE applications using this repository and boilerplate code

# app/

This is where all of your custom application code will go.
* `app/code/` is included in the PYTHONPATH for NVFLARE when runnning your application.
* `app/config/` contains define the components used for your application on both the server side and the client side

# jobs/job/

This is an artifact of how NVFLARE runs computations. An app needs to be submitted as a job. Simulator and POC mode use this folder during development.
When you make a change to either of the files in `app/config/` be sure to run `appToJob.sh` to copy the changes over.

# Developing for NVFLARE

[https://nvflare.readthedocs.io/en/2.4.0/programming_guide.html](https://nvflare.readthedocs.io/en/2.4.0/programming_guide.html)

The things you must know to make an NVFLARE app

- What is an NVFLARE component
- The configs define the components including the path to their respective python modules
- The necessary components and their python classes
  - Controller
  - Executor
  - Aggregator (not strictly necessary for all applications)
- How to implement their abstract methods
- How to use a Shareable
- How to use fl_context

## NVFLARE components

### Controller component

`Controller` is the central component that runs on the central server.
It manages the application's workflow. It distributes tasks to the sites to execute and handles dealing with responses for instance, directing them to an aggregator component,

### Executor component

`Executor` is what runs on the sites

The controller distributes tasks
Data is sent using shareabales

## Communication between components

Components communicate with shareables
They can also share fl_context

### Programming

NVFLARE components defined in

```
app/config/
--config_fed_client.json
--config_fed_server.json
```

#### Controller

[https://nvflare.readthedocs.io/en/main/apidocs/nvflare.apis.impl.controller.html](https://nvflare.readthedocs.io/en/main/apidocs/nvflare.apis.impl.controller.html)
The controller defines a workflow for the application.
It creates and distributes tasks, receives the results and proc
controller:
broadcast_and_wait
tasks

#### Executor

[https://nvflare.readthedocs.io/en/main/apidocs/nvflare.apis.executor.html](https://nvflare.readthedocs.io/en/main/apidocs/nvflare.apis.executor.html)
The execute method receives a task from the server and sends back a response by returning a Shareable

Class: Executor
Methods:
execute
returns: Shareable

#### Task

#### Shareable

# Our application development conventions:

## Relative paths

In NVFLARE simulator, NVFLARE POC mode, and NVFLARE production, the paths to data and parameters will be different
The boilerplate app provides an example of how to switch paths dynamically based on what environment the app is deployed in.

## Test data

Test data for each site as well as the parameters.json for a run will go in the test_data folder
When testing, the name of the site folder needs to match the name of the client

## Parameters.json

This is a JSON object the NVFLARE server will load and make available to all clients.
Its contents can be whatever you want to include in your computation. Your computation will be responsible for reading it.

## Test results