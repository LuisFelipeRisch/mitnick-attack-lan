# mitnick-attack-lan

### Sobre o Autor
Nome: Luis Felipe Risch

GRR: 20203940

### Sobre a Configuração do Ambiente
Foi disponibilizado um ambiente docker para uso. Desta forma, caso não tenha o docker instalado, é preciso que instale para que seja possível simular o ataque. Clique [aqui](https://docs.docker.com/engine/install/) e acesse as documentações de como instalar o docker em sua máquina.

Antes de rodar o docker compose, certifique-se que o seguinte comando 
```bash
echo '10.9.0.6' > /root/.rhosts
```

esteja presente na chave `command` do serviço `x-terminal` no arquivo `docker-compose.yml`. Este comando é necessário para dar acesso remoto, sem autenticação, ao `trusted-server` na `x-terminal`. Isso é um dos princípios do ataque mitnick, uma máquina confiável (A) pode acessar outra máquina (B), sem nenhuma autenticação, pois o ip da máquina A se encontra no arquivo `.rhosts` da máquina B. 

Tendo o docker instalado, na raíz do projeto rode o seguinte comando: 
```bash
sudo docker compose up
```

Agora, abra três terminais distintos e, em cada um destes, execute uma das três linhas de comando abaixo separadamente:
```bash
sudo docker exec -it seed-attacker bash # acessa a máquina atacante
```
```bash
sudo docker exec -it x-terminal-10.9.0.5 bash # acessa a máquina
```
```bash
sudo docker exec -it trusted-server-10.9.0.6 bash # acessa a máquina trusted-server
```
Por fim, na máquina `x-terminal` certifique-se que o ip da máquina `trusted-server` se encontra no arquivo `.rhosts`. Rode o seguinte comando: 

```bash
cat /root/.rhosts # deve retornar 10.9.0.6
```

### Sobre a execução do ataque
Na máquina `seed-attacker` rode o script `attack.py` que se encontra no diretório `volumes`. Execute o seguinte comando: 

```bash
python3 /volumes/attack.py
```

Se tudo tiver ocorrido bem, você deve ser capaz de ver a seguite mensagem em seu terminal: 

```txt
At this point, you may have remote access via rsh with xterminal. When this script stops running, just type on terminal the following command: rsh 10.9.0.5. Bye bye :)
```

O script é responsável por instalar a `backdoor` na máquina `x-terminal` através da personificação da máquina `trusted-server`. Você pode conferir isso executando o seguinte comando na máquina `x-terminal`, após a execução do script: 

```bash
cat /root/.rhosts
```

você vai perceber que foi adiciona um `+ +` no fim do arquivo. Isso significa que agora qualquer máquina pode acessar a máquina `x-terminal` remotamente, inclusive a máquina atacante. Para conferir isso, rode o seguinte comando na máquina `seed-attacker`: 

```bash
rsh 10.9.0.5
```

Pronto, agora você pode fazer qualquer coisa com a máquina `x-terminal`. 

Obs: Detalhes de implementações se encontram documentadas no código.




