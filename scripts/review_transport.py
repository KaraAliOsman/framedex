"""Local TCP relay preserving the public Supabase issuer inside Docker."""
import asyncio


async def connect(reader, writer):
    remote_reader, remote_writer = await asyncio.open_connection('host.docker.internal', 25361)

    async def transfer(source, destination):
        try:
            while data := await source.read(65536):
                destination.write(data)
                await destination.drain()
        finally:
            destination.close()

    await asyncio.gather(transfer(reader, remote_writer), transfer(remote_reader, writer))


async def main():
    server = await asyncio.start_server(connect, '127.0.0.1', 25361)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
