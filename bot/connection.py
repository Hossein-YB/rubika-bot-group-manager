from rubpy.network import Connection
import os
from rubpy.structs import results
from rubpy.gadgets import exceptions, methods


class CConnection(Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def c_upload_file(self, file, mime: str = None, file_name: str = None, chunk: int = 1048576 * 2,
                          callback=None, *args, **kwargs):
        if isinstance(file, str):
            if not os.path.exists(file):
                raise ValueError('file not found in the given path')
            if file_name is None:
                file_name = os.path.basename(file)

            with open(file, 'rb') as file:
                file = file.read()

        elif not isinstance(file, bytes):
            raise TypeError('file arg value must be file path or bytes')

        if file_name is None:
            raise ValueError('the file_name is not set')

        if mime is None:
            mime = file_name.split('.')[-1]

        result = await self.execute(
            methods.messages.RequestSendFile(
                mime=mime, size=len(file), file_name=file_name
            )
        )

        id = result.id
        index = 0
        dc_id = result.dc_id
        total = int(len(file) / chunk + 1)
        upload_url = result.upload_url
        access_hash_send = result.access_hash_send

        while index < total:
            data = file[index * chunk: index * chunk + chunk]
            try:
                result = await self._connection.post(
                    upload_url,
                    headers={
                        'auth': self._client._auth,
                        'file-id': id,
                        'total-part': str(total),
                        'part-number': str(index + 1),
                        'chunk-size': str(len(data)),
                        'access-hash-send': access_hash_send
                    },
                    data=data
                )
                result = result.json()
                if callable(callback):
                    try:
                        await callback(len(file), index * chunk)

                    except exceptions.CancelledError:
                        return None

                    except Exception:
                        pass

                index += 1
            except Exception:
                pass

        status = result['status']
        status_det = result['status_det']
        if status == 'OK' and status_det == 'OK':
            result = {
                'mime': mime,
                'size': len(file),
                'dc_id': dc_id,
                'file_id': id,
                'file_name': file_name,
                'access_hash_rec': result['data']['access_hash_rec']
            }

            return results('UploadFile', result)

        self._client._logger.debug('upload failed', extra={'data': result})
        raise exceptions(status_det)(result, request=result)
