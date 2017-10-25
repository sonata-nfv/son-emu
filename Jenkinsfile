properties([
    parameters([
        string(defaultValue: env.BRANCH_NAME, description: '', name: 'GERRIT_BRANCH'),
        string(defaultValue: 'osm/vim-emu', description: '', name: 'GERRIT_PROJECT'),
        string(defaultValue: env.GERRIT_REFSPEC, description: '', name: 'GERRIT_REFSPEC'),
        string(defaultValue: env.GERRIT_PATCHSET_REVISION, description: '', name: 'GERRIT_PATCHSET_REVISION'),
        string(defaultValue: 'https://osm.etsi.org/gerrit', description: '', name: 'PROJECT_URL_PREFIX'),
        booleanParam(defaultValue: false, description: '', name: 'TEST_INSTALL'),
        string(defaultValue: 'artifactory-osm', description: '', name: 'ARTIFACTORY_SERVER'),
    ])
])

def devops_checkout() {
    dir('devops') {
        git url: "${PROJECT_URL_PREFIX}/osm/devops", branch: params.GERRIT_BRANCH
    }
}

node('docker') {
    checkout scm
    devops_checkout()

    // vim-emu: We need to use privileged mode, docker.sock, and host pids for the container
    // to test the emulator. Also needs -u 0:0 (root user inside container).
    docker_args = "--privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock -u 0:0"

    ci_helper = load "devops/jenkins/ci-pipelines/ci_stage_2.groovy"
    ci_helper.ci_pipeline( 'vim-emu',
                           params.PROJECT_URL_PREFIX,
                           params.GERRIT_PROJECT,
                           params.GERRIT_BRANCH,
                           params.GERRIT_REFSPEC,
                           params.GERRIT_PATCHSET_REVISION,
                           params.TEST_INSTALL,
                           params.ARTIFACTORY_SERVER,
                           docker_args)
}
