import os
from dotenv import load_dotenv
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow
from oauth2client.file import Storage
from apiclient.discovery import build
from apiclient.http import MediaIoBaseDownload
from io import FileIO
import httplib2

from youtube_analytics_automation.utils import redshift 

load_dotenv() 
USER = os.getenv("REDSHIFT_USER")
PASSWORD = os.getenv("REDSHIFT_PASSWORD")
HOST = os.getenv("REDSHIFT_HOST")
DATABASE = os.getenv("YOUTUBE_DATABASE")
PORT = '5439'
TABLE_NAME = 'youtube_reporting'

# SECRETS AND CREDENTIALS
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE")
STORAGE_CREDENTIALS_FILE = os.getenv("STORAGE_CREDENTIALS_FILE")

con = redshift.connect(USER, PASSWORD, HOST, DATABASE, port=PORT)
ex = con.execute

#----------------------------------------------------------------
def connect_to_reporting_api():

    SERVICE_NAME = "youtubereporting"
    VERSION = 'v1'
    SCOPE = [
        'https://www.googleapis.com/auth/yt-analytics.readonly',
        'https://www.googleapis.com/auth/yt-analytics-monetary.readonly'
    ]
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=SCOPE,
            message="Ya did sumpin' wrong, Bub!")
    storage = Storage(STORAGE_CREDENTIALS_FILE)
    credentials = storage.get()   # Returns None if the file doesn't exist
    if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage)
    # Return Connection
    report = build(SERVICE_NAME,  VERSION,  http=credentials.authorize(httplib2.Http()))
    return report


#----------------------------------------------------------------
def list_report_types(report, owner_id, pretty=False):
    report_types = report.reportTypes().list(
            onBehalfOfContentOwner=owner_id).execute()['reportTypes']
    if pretty:
        report_types = {item['name']: item['id'] for item in report_types}
    return report_types

#----------------------------------------------------------------
def list_jobs(report, owner_id, pretty=False, id2name=False):
    list_of_jobs = report.jobs().list(
            onBehalfOfContentOwner = owner_id).execute()['jobs']
    # Format Output?
    if id2name: pretty=True
    if pretty:
        if id2name:
            list_of_jobs = {job['id']: job['name'] for job in list_of_jobs}
        else:
            list_of_jobs = {job['name']: job['id'] for job in list_of_jobs}
    return list_of_jobs


#----------------------------------------------------------------
# NOTE
#----------------------------------------------------------------
# The list_inactive_reports, initiate_a_job, download_from_single_date, 
# and download_single_job_report functions below worked against the 
# 2016–2017 YouTube Reporting API. At that time, list_jobs() and 
# list_report_types() did not require an explicit contentOwnerId 
# (owner_id), which I've since learned has changed.
# 
# IN OTHER WORDS: This code is retained for historical/portfolio purposes 
# and is not expected to run against the current API without modification.
#----------------------------------------------------------------
#----------------------------------------------------------------
#----------------------------------------------------------------
def list_inactive_reports(report):
    # Check if this job is already running
    job_list = [item['reportTypeId'] for item in list_jobs(report)]
    report_type_list = [item['id'] for item in list_report_types(report)]
    return set(report_type_list).difference(job_list)

#----------------------------------------------------------------
def initiate_a_job(
    report, 
    report_type, # dict or ID
    owner_id
):
    if isinstance(report_type,dict):
        report_type_id = report_type['id']
        report_name = report_type['name']
    elif isinstance(report_type,str):
        reportList = list_report_types(report)
        report_type_id = report_type
        report_name = [item['name'] for item in reportList 
            if item['id'] == report_type_id][0]
    # Check if this job is already running
    job_list = list_jobs(report)
    job_exists = [True for item in job_list if item['reportTypeId']==report_type_id]
    if job_exists:
        print('The job already exists.')
    else:
        report.jobs().create(
            body = {'reportTypeId': report_type_id, 'name': report_name},
            onBehalfOfContentOwner=owner_id
            ).execute()
        print('The '+report_name.title()+' report has been initiated.')

#----------------------------------------------------------------
def list_job_reports(
    report, 
    job_id, 
    owner_id, 
    start_time_before=None,
    start_time_at_or_after=None, 
    created_after=None,
):
    # Initialize List of Reports
    list_of_reports = []
    # Send First Request (Max 100 Reports Returned)
    request = report.jobs().reports().list(
            jobId = job_id,
            startTimeBefore = start_time_before,
            startTimeAtOrAfter = start_time_at_or_after,
            createdAfter = created_after,
            onBehalfOfContentOwner = owner_id)
    response = request.execute()
    list_of_reports += response['reports']
    # Send Requests until no more reports
    while request:
        request = report.jobs().reports().list_next(request,response)
        if request:
            response = request.execute()
            list_of_reports += response['reports']
    return list_of_reports


#----------------------------------------------------------------
def download_single_job_report(
        report,
        job_report,
        report_name=None,
        chunksize = 1e7,
        testing=False
):
    """
    The idea here is that you already obtained a list of
    reports and are now downloading the reports on that list
    one by one.
    """
    # SET UP TABLE NAME
    if report_name is None:
        job_id = job_report['jobId']
        list_of_jobs = list_jobs(report, id2name=True)
        report_name = '_'.join(list_of_jobs[job_id].lower().split())
        output = report_name
    else:
        output = None

    # SET UP FILE NAME
    REPORT_DATE = job_report['startTime'][0:10]
    AS_ON_DATE  = job_report['createTime'][0:10]
    FILENAME    = TABLE_NAME+'__'+REPORT_DATE+'_ason_'+AS_ON_DATE+'.csv'

    # STREAM/DOWNLOAD THE REPORT
    if not testing:
        # UPDATE USER
        print('Downloading the', REPORT_DATE, 'Report (created on,', AS_ON_DATE, ')')
        # SET UP DOWNLOAD
        request = report.media().download(resourceName="csv")
        request.uri = job_report['downloadUrl']
        fh = FileIO(FILENAME, mode='wb')
        downloader = MediaIoBaseDownload(fh, request, chunksize=chunksize)
        done = False
        # BEGIN DOWNLOAD
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                print("Download %d%%." % int(status.progress() * 100))
        # RETURN SOME INFO
        print("Download Complete!\n")
    else:
        # RETURN SOME INFO
        print(TABLE_NAME+'\n'+FILENAME)
    return output


#----------------------------------------------------------------
def download_list_of_job_reports(
        report,
        lojr_or_job_id,
        owner_id,
        start_time_before=None,
        start_time_at_or_after=None,
        created_after=None,
):
    # Either pass in a list of job reports (LOJR) or a jobId
    if isinstance(lojr_or_job_id,str):
        job_id = lojr_or_job_id
        list_of_job_reports = list_job_reports(
            report,
            job_id,
            start_time_before=start_time_before,
            start_time_at_or_after=start_time_at_or_after,
            created_after=created_after,
            owner_id = owner_id)
    elif isinstance(lojr_or_job_id,list):
        list_of_job_reports = lojr_or_job_id
    else:
        raise TypeError(f"Expected str or list, got {type(lojr_or_job_id).__name__}")
    # Begin Downloading
    num_jobs = len(list_of_job_reports)
    ticker = 1
    print(str(ticker)+" of " + str(num_jobs))
    report_name = download_single_job_report(report, list_of_job_reports[0])
    for job_report in list_of_job_reports[1:]:
        ticker += 1
        print(str(ticker)+" of " + str(num_jobs))
        download_single_job_report(report, job_report, report_name)


#---------------------------------------------------------------
def download_from_single_date(
    sample_date, 
    job_id=None, 
    rep_name=None, 
    chunksize=1e7,
):
    if job_id is None:
        job_list = list_jobs(rep_name)
        job_id = [item['id'] for item in job_list]
        rep_name = [item['name'] for item in job_list]
    if str(type(job_id)).split("'")[1] == "str":
        job_id = [job_id]
    if rep_name is None:
        rep_name = 'requested'
    assert len(job_id) == len(rep_name), 'Must have same number of Job Ids and Report Names.'
    for idx in range(len(job_id)):
        jobs = list_job_reports(rep_name, job_id[idx])
        sample_job = [item for item in jobs if item['startTime'][:10]==sample_date][0]
        print('Accessing the '+rep_name[idx]+' report')
        download_single_job_report(rep_name, sample_job, chunksize=chunksize)