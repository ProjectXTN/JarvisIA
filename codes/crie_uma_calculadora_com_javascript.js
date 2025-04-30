javascript class Calculadora {
    constructor() {
        this.historico = [];
    }
    somar(num1, num2) {
        const resultado = num1 + num2;
        this.historico.push(`Somou ${num1} e ${num2}, resultado: ${resultado}`);
        return resultado;
    }
    subtrair(num1, num2) {
        const resultado = num1 - num2;
        this.historico.push(`Subtraiu ${num2} de ${num1}, resultado: ${resultado}`);
        return resultado;
    }
    multiplicar(num1, num2) {
        const resultado = num1 * num2;
        this.historico.push(`Multiplicou ${num1} por ${num2}, resultado: ${resultado}`);
        return resultado;
    }
    dividir(num1, num2) {
        if (num2 === 0) {
            throw new Error('Divisão por zero');
        }
        const resultado = num1 / num2;
        this.historico.push(`Dividiu ${num1} por ${num2}, resultado: ${resultado}`);
        return resultado;
    }
    getHistorico() {
        return this.historico;
    }
}
const calculadora = new Calculadora();

function executarOperacao(operacao, num1, num2) {
    switch (operacao) {
        case 'somar':
            return calculadora.somar(num1, num2);
        case 'subtrair':
            return calculadora.subtrair(num1, num2);
        case 'multiplicar':
            return calculadora.multiplicar(num1, num2);
        case 'dividir':
            return calculadora.dividir(num1, num2);
        default:
            throw new Error('Operação inválida');
    }
}

function main() {
    const num1 = parseFloat(prompt('Digite o primeiro número:'));
    const operacao = prompt('Digite a operação (+, -, *, /):');
    const num2 = parseFloat(prompt('Digite o segundo número:'));
    try {
        const resultado = executarOperacao(operacao, num1, num2);
        alert(`Resultado: ${resultado}`);
        console.log(calculadora.getHistorico());
    } catch (error) {
        alert(error.message);
    }
}
main();