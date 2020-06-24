from grpc_tools import protoc

protoc.main((
    '',
    '-I../protos',
    '--python_out=.',
    '--grpc_python_out=.',
    '../protos/gps.proto',
))

protoc.main((
    '',
    '-I../protos',
    '--python_out=.',
    '--grpc_python_out=.',
    '../protos/imu.proto',
))

protoc.main((
    '',
    '-I../protos',
    '--python_out=.',
    '--grpc_python_out=.',
    '../protos/easydriver.proto',
))