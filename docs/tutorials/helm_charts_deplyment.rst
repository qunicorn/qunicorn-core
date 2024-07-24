A tutorial on how to deploy the helm charts
=====================

## helm installation

[Helm](https://helm.sh) must be installed to use the charts.  Please refer to Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, then we need:

To install the <chart-name> chart:

`cd <helm-chart-folder>`

`helm install <my-chart-name> .`

To uninstall the chart:

`helm delete <my-chart-name>`


------------------------------------------------------------------------------------------------------------------------------------


##Converting YAML Files Into Helm Charts

###Using helmify

1) Step1 . Installation of helmify

2) Step2. Convert YAML files to Helm chart
For single yaml file: 

`cat <your-yamlfile-name>.yaml | helmify <chart-name>`

From directory with yamls:

`awk 'FNR==1 && NR!=1  {print "---"}{print}' /<my_directory>/*.yaml | helmify <helmchart-folder-name>`





