import subprocess
import argparse
from urllib.parse import urlparse
from repo2docker.__main__ import make_r2d

def resolve_ref(repo_url, ref):
    """
    Return resolved commit hash for branch / tag.

    Return ref unmodified if branch / tag isn't found
    """
    stdout = subprocess.check_output(
        ['git', 'ls-remote', repo_url]
    ).decode()
    # ls-remote output looks like this:
    # <hash>\t<ref>\n
    # <hash>\t<ref>\n
    # Since our ref can be a tag (so refs/tags/<ref>) or branch
    # (so refs/head/<ref>), we get all refs and check if either
    # exists
    all_refs = [l.split('\t') for l in stdout.strip().split('\n')]
    for hash, ref in all_refs:
        if ref in (f'refs/heads/{ref}', f'refs/heads/{ref}'):
            return hash

    if stdout:
        return stdout.split()[0]
    return ref

def readable_image_name(repo, resolved_ref):
    """
    Make a readable image name for repo and ref.

    This *is* going to cause collisions!
    """
    parts = urlparse(repo)
    return '{}-{}:{}'.format(
        parts.netloc,
        parts.path.replace('/', '-'),
        resolved_ref
    )


def main():
    r2d = make_r2d()
    # charliecloud doesn't read ENV from r2d
    # so we explicitly save it and load it back
    r2d.appendix = r"""
    USER root
    # Prefixing with 000- means bash -l will source it first
    RUN ln -s /environment /etc/profile.d/000-repo2docker-env.sh
    USER ${NB_USER}
    """

    r2d.initialize()
    r2d.build()
    
    r2d.log.info('Exporting built image to tar\n')
    subprocess.check_call([
        'ch-docker2tar',
        r2d.output_image_spec,
        '.'
    ])

if __name__ == '__main__':
    main()
