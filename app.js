const API_URL = "https://ygu6o16mh8.execute-api.us-east-1.amazonaws.com";

const message = document.querySelector("#message");
const deployments = document.querySelector("#deployments");
const summary = document.querySelector("#summary");

document.querySelector("#refresh").addEventListener("click", loadDeployments);

async function loadDeployments() {
  message.textContent = "Loading deployment records...";
  try {
    const response = await fetch(API_URL);
    if (!response.ok) throw new Error(`Dashboard API returned ${response.status}`);
    const data = await response.json();
    render(data.services || []);
    message.textContent = `Last refreshed ${new Date().toLocaleString()}`;
  } catch (error) {
    deployments.replaceChildren();
    summary.replaceChildren();
    message.textContent = `Unable to load deployment records: ${error.message}`;
  }
}

function render(services) {
  // Get only the latest deployment for each service (across all environments)
  const latestByService = services.reduce((result, service) => {
    const key = service.service_name;
    if (!result[key] || service.deployed_at > result[key].deployed_at) {
      result[key] = service;
    }
    return result;
  }, {});

  // Sort by service name
  const sortedDeployments = Object.values(latestByService).sort((a, b) =>
    a.service_name.localeCompare(b.service_name)
  );

  // Count services per environment
  const counts = sortedDeployments.reduce((result, service) => {
    const environment = service.environment || "unknown";
    result[environment] = (result[environment] || 0) + 1;
    return result;
  }, {});

  summary.replaceChildren(
    ...["dev", "test", "staging", "prod"].map((environment) => {
      const card = document.createElement("div");
      card.className = `summary-card ${environment}`;
      card.innerHTML = `<strong>${environment.toUpperCase()}</strong><span>${counts[environment] || 0} service(s)</span>`;
      return card;
    }),
  );

  deployments.replaceChildren(
    ...sortedDeployments.map((service) => {
      const row = document.createElement("tr");
      const commitSha = service.git_commit_sha || "unknown";
      const commitShort = commitSha.slice(0, 8);
      const repoName = `wgu-${service.service_name}`;
      const commitLink = commitSha !== "unknown"
        ? `<a href="https://github.com/adhikarim/${escapeHtml(repoName)}/commit/${escapeHtml(commitSha)}" target="_blank" rel="noopener noreferrer">${escapeHtml(commitShort)}</a>`
        : escapeHtml(commitShort);

      const deployedAt = service.deployed_at !== "unknown"
        ? new Date(service.deployed_at).toLocaleString()
        : service.deployed_at;

      row.innerHTML = `
        <td>${escapeHtml(service.service_name)}</td>
        <td><span class="environment ${escapeHtml(service.environment)}">${escapeHtml(service.environment).toUpperCase()}</span></td>
        <td><span class="status ${escapeHtml(service.status)}">${escapeHtml(service.status).toUpperCase()}</span></td>
        <td>${escapeHtml(service.version)}</td>
        <td class="commit">${commitLink}</td>
        <td>${escapeHtml(deployedAt)}</td>
      `;
      return row;
    }),
  );
}

function escapeHtml(value = "unknown") {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[character]));
}

loadDeployments();
