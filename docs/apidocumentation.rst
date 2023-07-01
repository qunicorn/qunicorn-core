API Documentation
=========================================

Generated Documentation
-------

Below you can find a generated Documentation of the API. 

* `Api documentation <api.html>`_

=====

Structure Overview
-------

This is how the structure of the API looks like.

* api-root 
    * GET /
* jobmanager-api
    * GET       /jobs/
    * POST      /jobs/
    * GET       /jobs/{job_id}/
    * POST      /jobs/{job_id}/
    * PUT       /jobs/{job_id}/
    * DELETE    /jobs/{job_id}/
* devices-api
    * GET       /devices/
    * GET       /devices/{device_id}/
    * GET       /devices/{device_id}/status
    * GET       /devices/{device_id}/calibration
    * GET       /devices/{device_id}/jobs
* deployment-api
    * GET       /deployments/
    * POST      /deployments/
    * GET       /deployments/{deployment_id}/
    * PUT       /deployments/{deployment_id}/
    * PATCH     /deployments/{deployment_id}/
    * DELETE    /deployments/{deployment_id}/
    * GET       /deployments/{deployment_id}/jobs
* services-api
    * GET       /services/
    * GET       /services/{service_id}/
* users-api
    * GET       /users/
    * GET       /users/{user_id}/