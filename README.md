# Deployment Dashboard

Static GitHub Pages frontend for the AWS deployment status API.

## Configure

Replace `REPLACE_WITH_DASHBOARD_API_URL` in `app.js` with the
`deployment_dashboard_url` output from the AWS shared Terraform stack. Set the
AWS stack's `dashboard_origin` to this site's GitHub Pages URL.

## Publish

Enable GitHub Pages for the repository using the `main` branch and root folder.
