# Copyright (c) OpenMMLab. All rights reserved.
import os
import time


def cmd_result(txt: str):
    cmd = os.popen(txt)
    return cmd.read().rstrip().lstrip()


def get_job(argv) -> int:
    # get nprocs, if user not specified, use max(2, nproc-1)
    job = 2
    if len(argv) <= 1:
        print('your can use `python3 {} N` to set make -j [N]'.format(argv[0]))
        nproc = cmd_result('nproc')
        if nproc is not None and len(nproc) > 0:
            job = max(int(nproc) - 1, 2)
        else:
            job = 2
    else:
        job = int(argv[1])
    return job


def version_major(txt: str) -> int:
    return int(txt.split('.')[0])


def version_minor(txt: str) -> int:
    return int(txt.split('.')[1])


def cu_version_name(version: str) -> str:
    versions = version.split('.')
    return 'cu' + versions[0] + versions[1]


def simple_check_install(bin: str, sudo: str) -> str:
    result = cmd_result('which {}'.format(bin))
    if result is None or len(result) < 1:
        print('{} not found, try install {} ..'.format(bin, bin), end='')
        os.system('{} apt install {} -y'.format(sudo, bin))
        result = cmd_result('which {}'.format(bin))
        if result is None or len(result) < 1:
            print('Check {} failed.'.format(bin))
            return None
        print('success')
    return result


def ensure_base_env(work_dir, dep_dir):
    description = """
    check python, root, pytorch version, auto install these binary:

    * make
    * g++-7
    * git
    * wget
    * unzip
    * opencv
    * mmcv (not compulsory)
    """

    envs = []
    print('-' * 10 + 'ensure base env' + '-' * 10)
    print(description)

    os.system('python3 -m ensurepip')
    os.system('python3 -m pip install wheel')

    sudo = 'sudo'
    if 'root' in cmd_result('whoami'):
        sudo = ''

    # check ubuntu
    ubuntu = cmd_result(
        """ lsb_release -a 2>/dev/null | grep "Release" | tail -n 1 | awk '{print $NF}' """  # noqa: E501
    )

    # check cmake version
    cmake = cmd_result('which cmake')
    if cmake is None or len(cmake) < 1:
        print('cmake not found, try install cmake ..', end='')
        os.system('python3 -m pip install cmake>=3.14.0')

        cmake = cmd_result('which cmake')
        if cmake is None or len(cmake) < 1:
            env = 'export PATH=${PATH}:~/.local/bin'
            os.system(env)
            envs.append(env)

            cmake = cmd_result('which cmake')
            if cmake is None or len(cmake) < 1:
                print('Check cmake failed.')
                return -1, envs
        print('success')

    # check  make
    make = cmd_result('which make')
    if make is None or len(make) < 1:
        print('make not found, try install make ..', end='')
        os.system('{} apt update --fix-missing'.format(sudo))

        os.system(
            '{} DEBIAN_FRONTEND="noninteractive"  apt install make'.format(
                sudo))
        make = cmd_result('which make')
        if make is None or len(make) < 1:
            print('Check make failed.')
            return -1, envs
        print('success')

    # check g++ version
    gplus = cmd_result('which g++-7')
    if gplus is None or len(gplus) < 1:
        # install g++
        print('g++-7 not found, try install g++-7 ..', end='')
        os.system(
            '{} DEBIAN_FRONTEND="noninteractive" apt install software-properties-common -y'  # noqa: E501
            .format(sudo))  # noqa: E501
        os.system('{} apt update'.format(sudo))
        if ubuntu is None or len(ubuntu) < 1 or version_major(ubuntu) <= 18:
            os.system(
                '{} add-apt-repository ppa:ubuntu-toolchain-r/test -y'.format(
                    sudo))
        os.system('{} apt install gcc-7 g++-7 -y'.format(sudo))

        gplus = cmd_result('which g++-7')
        if gplus is None or len(gplus) < 1:
            print('Check g++-7 failed.')
            return -1, envs
        os.system(
            '{} update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 200'  # noqa: E501
            .format(sudo))
        os.system(
            '{} update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-7 200'  # noqa: E501
            .format(sudo))
        print('success')

    # wget
    wget = simple_check_install('wget', sudo)

    # check torch and mmcv, we try to install mmcv, it is not compulsory
    mmcv_version = None
    torch_version = None
    try:
        import torch
        torch_version = torch.__version__

        try:
            import mmcv
            mmcv_version = mmcv.__version__
        except Exception:
            # install mmcv
            print('mmcv not found, try install mmcv ..', end='')
            os.system('python3 -m pip install -U openmim')
            os.system('mim install mmcv-full==1.5.1')
    except Exception:
        pass

    # git
    git = simple_check_install('git', sudo)

    # unzip
    unzip = simple_check_install('unzip', sudo)

    # opencv
    ocv = cmd_result('which opencv_version')
    if ocv is None or len(ocv) < 1:
        print('ocv not found, try install git ..', end='')
        os.system(
            '{} add-apt-repository ppa:ignaciovizzo/opencv3-nonfree -y'.format(
                sudo))
        os.system('{} apt update'.format(sudo))
        os.system(
            '{} DEBIAN_FRONTEND="noninteractive"  apt install libopencv-dev -y'
            .format(sudo))

        ocv = cmd_result('which opencv_version')
        if ocv is None or len(ocv) < 1:
            print('Check ocv failed.')
            return -1, envs
        print('success')

    # print all
    print('ubuntu \t\t:{}'.format(ubuntu))

    # check python
    print('python bin\t:{}'.format(cmd_result('which python3')))
    print('python version\t:{}'.format(
        cmd_result("python3 --version | awk '{print $2}'")))

    print('cmake bin\t:{}'.format(cmake))
    print('cmake version\t:{}'.format(
        cmd_result("cmake --version | head -n 1 | awk '{print $3}'")))

    print('make bin\t:{}'.format(make))
    print('make version\t:{}'.format(
        cmd_result(" make --version  | head -n 1 | awk '{print $3}' ")))

    print('wget bin\t:{}'.format(wget))
    print('g++-7 bin\t:{}'.format(gplus))

    print('mmcv version\t:{}'.format(mmcv_version))
    if mmcv_version is None:
        print('\t please install an mm serials algorithm later.')
        time.sleep(2)

    print('torch version\t:{}'.format(torch_version))
    if torch_version is None:
        print('\t please install pytorch later.')
        time.sleep(2)

    print('ocv version\t:{}'.format(cmd_result('opencv_version')))

    print('git bin\t\t:{}'.format(git))
    print('git version\t:{}'.format(
        cmd_result("git --version | awk '{print $3}' ")))
    print('unzip bin\t:{}'.format(unzip))
    # work dir
    print('work dir \t:{}'.format(work_dir))
    # dep dir
    print('dep dir \t:{}'.format(dep_dir))

    print('\n')
    return 0, envs
