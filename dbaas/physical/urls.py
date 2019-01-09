# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url


urlpatterns = patterns(
    'physical.views',
    url(r'^engines_by_env/(?P<environment_id>\d+)/$', "engines_by_env"),
    url(r'^topology_by_eng/(?P<engine_id>\d+)/$', "topology_by_eng"),
    url(r'^plans_by_engine/(?P<engine_id>\d+)_(?P<environment_id>\d+)/$', "plans_by_engine"),
    url(r'^offerings_by_env/(?P<environment_id>\d+)/$', "offerings_by_env"),
    url(r'^plans_details/$', "plans_details"),
)
