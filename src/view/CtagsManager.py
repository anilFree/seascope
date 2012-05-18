import subprocess

def _eintr_retry_call(func, *args):
	while True:
		try:
			return func(*args)
		except OSError, e:
			if e.errno == errno.EINTR:
				continue
			raise

def ct_query(filename):
	cmd = 'ctags -n -u --fields=+K -f -'
	args = cmd.split()
	args.append(filename)
	try:
		proc = subprocess.Popen(args, stdout=subprocess.PIPE)
		(out_data, err_data) = _eintr_retry_call(proc.communicate)
		out_data = out_data.split('\n')
	except Exception as e:
		out_data =  [
				'Failed to run ctags cmd\tignore\t0;\t ',
				'cmd: %s\tignore\t0;\t ' % ' '.join(args),
				'error: %s\tignore\t0;\t ' % str(e),
				'ctags not installed ?\tignore\t0;\t ',
			]
	res = []
	for line in out_data:
		if (line == ''):
			break
		line = line.split('\t')
		num = line[2].split(';', 1)[0]
		line = [line[0], num, line[3]]
		res.append(line)
	return res
