import six

from egnyte import base, const, exc

class Audits(base.HasClient):
    """
    This resource is used to generated various kinds of audit reports.
    """
    _url_logins = "pubapi/v1/audit/logins"
    _url_files = "pubapi/v1/audit/files"
    _url_permissions = "pubapi/v1/audit/permissions"

    def _job_id(self, response):
        json = exc.default.check_json_response(response)
        return json['id']

    def logins(self, format, date_start, date_end, events, access_points=None, users=None):
        """
        Generate login report.
        Parameters:
          format: 'csv' or 'json'
          date_start: datetime.date - first day report should cover
          date_end: datetime.date - last day report should cover

        """
        json = dict(format=format,
                    date_start=base.date_format(date_start),
                    date_end=base.date_format(date_end),
                    events=list(events))
        if access_points is not None:
            json['access_points'] = list(access_points)
        if users is not None:
            json['users'] = list(users)
        r = self._client.POST(self._client.get_url(self._url_logins), json)
        return AuditReport(self._client, id=self._job_id(r), format=format, type='logins')

    def files(self, format, date_start, date_end, folders=None, file=None, users=None, transaction_type=None):
        """
        Generate files report.
        Parameters:
          format: 'csv' or 'json'
          date_start: datetime.date - first day report should cover
          date_end: datetime.date - last day report should cover

        """
        json = dict(format=format,
                    date_start=base.date_format(date_start),
                    date_end=base.date_format(date_end))
        if folders is not None:
            json['folders'] = list(folders)
        if file is not None:
            json['file'] = file
        if users is not None:
            json['users'] = list(users)
        if transaction_type is not None:
            json['transaction_type'] = list(transaction_type)
        r = self._client.POST(self._client.get_url(self._url_files), json)
        return AuditReport(self._client, id=self._job_id(r), format=format, type='files')

    def permissions(self, format, date_start, date_end, folders, assigners, assignee_users, assignee_groups):
        """
        Generate permissions report.
        Parameters:
          format: 'csv' or 'json'
          date_start: datetime.date - first day report should cover
          date_end: datetime.date - last day report should cover

        """
        json = dict(format=format,
                    date_start=base.date_format(date_start),
                    date_end=base.date_format(date_end),
                    folders=list(folders),
                    assigners=list(assigners),
                    assignee_users=list(assignee_users),
                    assignee_groups=list(assignee_groups))
        r = self._client.POST(self._client.get_url(self._url_permissions), json)
        return AuditReport(self._client, id=self._job_id(r), format=format, type='permissions')


class AuditReport(base.Resource):
    _url_template = "pubapi/v1/audit/jobs/%(id)s"
    _url_template_completed = "pubapi/v1/audit/%(type)s/%(id)s"
    _lazy_attributes = {'status'}

    def is_ready(self):
        self.check()
        return self.status == 'completed'

    def download(self):
        url = self._client.get_url(self._url_template_completed, type=self.type, id=self.id)
        r = self._client.GET(url, stream=True)
        exc.default.check_response(r)
        return base.FileDownload(r)

    def json(self):
        url = self._client.get_url(self._url_template_completed, type=self.type, id=self.id)
        r = self._client.GET(url)
        return exc.default.check_json_response(r)
