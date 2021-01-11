class Client:
    @staticmethod
    def set_404_for_text(response, **kwargs):
        """Validate that unwanted text is not in response text."""
        if "foo" or "baz" in response.text:
            response.status_code = 404
        return response

    def get(self):
        with requests.Session() as session:
            session.hooks['response'].append(set_404_for_text)
            session.mount("https://bar.com", adapter=HTTPAdapter(max_retries=3))
            resp = session.get("https://bar.com")
            resp.raise_for_status()

        return resp