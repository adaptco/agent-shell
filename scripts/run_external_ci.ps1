param(
    [string]$Repo = "",
    [string]$Sha = "",
    [string]$Context = "external-ci",
    [string]$Command = "pytest -q"
)

if ([string]::IsNullOrWhiteSpace($Repo)) {
    $Repo = $env:GITHUB_REPOSITORY
}

if ([string]::IsNullOrWhiteSpace($Sha)) {
    $Sha = $env:GITHUB_SHA
}

if ([string]::IsNullOrWhiteSpace($Repo)) {
    $origin = (git config --get remote.origin.url).Trim()
    if ($origin -match 'github\.com[:/](.+/.+?)(\.git)?$') {
        $Repo = $matches[1]
    } else {
        throw "Could not infer repo slug from origin URL. Pass -Repo owner/name."
    }
}

if ([string]::IsNullOrWhiteSpace($Sha)) {
    $Sha = (git rev-parse HEAD).Trim()
}

python -m runtime.external_ci --repo $Repo --sha $Sha --context $Context --command $Command
