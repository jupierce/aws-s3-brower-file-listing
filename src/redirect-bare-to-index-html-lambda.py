# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import boto3
from urllib.parse import unquote

# Intercepts a response from S3 saying that a file is not found.
# The function will check S3 to see if the path specified in the URL
# refers to a valid "directory" prefix. If it does, the user will be
# redirected to the URL followed by a trailing "/" so that they will
# receive a directory listing instead of an error.

def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']
    uri = request['uri']
    response = event['Records'][0]['cf']['response']

    if int(response['status']) == 403:  # This is basically file-not-found from s3 if the user is authenticated

        if uri.endswith('/') or uri.endswith('/index.html'):
            # Nothing to do. This should have already hit the index.html
            return response

        # Let's see if a s3 key prefix of this name exists
        bucket_name = '${S3Bucket}'
        s3 = boto3.resource('s3', region_name='${AWS::Region}')
        s3_conn = boto3.client('s3')
        prefix = unquote(uri.lstrip('/'))  # URL escaped chars like "%2B" need to be converted to + for s3 API query.
        s3_result = s3_conn.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter="/")

        if s3_result.get('CommonPrefixes', []) or s3_result.get('Contents', []):
            # print(f'Redirecting because: {s3_result}')
            # If there are "sub-directories" or "files" in this directory, redirect with a trailing slash
            # So that the user will get a directory listing.
            host = request['headers']['host'][0]['value']
            # Otherwise, maybe the caller entered a directory name without
            # a trailing slash and it is not found. Make another attempt with a
            # trailing slash which should trigger the lookup of uri/index.html
            # if it exists.
            response['status'] = 302
            response['statusDescription'] = 'Found'
            response['body'] = ''
            response['headers']['location'] = [{'key': 'Location', 'value': f'{uri}/'}]

    return response
