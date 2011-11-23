import subprocess

def ct_query(filename):
	cmd = 'ctags -n -u --fields=+K -f -'
	args = cmd.split()
	args.append(filename)
	proc = subprocess.Popen(args, stdout=subprocess.PIPE)
	(out_data, err_data) = proc.communicate()
	out_data = out_data.split('\n')
	res = []
	for line in out_data:
		if (line == ''):
			break
		line = line.split('\t')
		num = line[2].split(';', 1)[0]
		line = [line[0], num, line[3]]
		res.append(line)
	return res
