# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
from django_services.api import DjangoServiceAPI, register
from django.http import HttpResponse
from django.http import Http404
from rest_framework.decorators import link
from rest_framework.response import Response
from base.models import Database
from base.driver.factory import DriverFactory
from .service.environment import EnvironmentService
from .service.node import NodeService
from .service.instance import InstanceService
from .service.database import DatabaseService
from .service.credential import CredentialService
from .service.engine import EngineService, EngineTypeService
from .serializers import EnvironmentSerializer, NodeSerializer, InstanceSerializer, \
                        DatabaseSerializer, CredentialSerializer, EngineSerializer, EngineTypeSerializer


class EnvironmentAPI(DjangoServiceAPI):
    serializer_class = EnvironmentSerializer
    service_class = EnvironmentService


class NodeAPI(DjangoServiceAPI):
    serializer_class = NodeSerializer
    service_class = NodeService


class InstanceAPI(DjangoServiceAPI):

    serializer_class = InstanceSerializer
    service_class = InstanceService
    operations = ('list', 'retrieve', 'create', 'update', 'destroy')


class DatabaseAPI(DjangoServiceAPI):
    serializer_class = DatabaseSerializer
    service_class = DatabaseService

    @link()
    def status(self, request, pk):
        """ Status of DB """
        try:
            db = Database.objects.get(pk=pk)
            instance = db.instance
            DriverFactory.factory(instance)
            return Response(
                {'status': 'WORKING'},
                status='200')
        except Database.DoesNotExist:
            return Response(
                {'status': 'Database does not exist.'},
                status='404')
        except Exception as e:
            return Response(
                {'status': 'Unknown error. %s (%s)' % (e.message, type(e))},
                status='500')


class CredentialAPI(DjangoServiceAPI):
    serializer_class = CredentialSerializer
    service_class = CredentialService


class EngineAPI(DjangoServiceAPI):
    serializer_class = EngineSerializer
    service_class = EngineService


class EngineTypeAPI(DjangoServiceAPI):
    serializer_class = EngineTypeSerializer
    service_class = EngineTypeService


register('environment', EnvironmentAPI)
register('node', NodeAPI)
register('instance', InstanceAPI)
register('database', DatabaseAPI)
register('credential', CredentialAPI)
register('engine', EngineAPI)
register('enginetype', EngineTypeAPI)

