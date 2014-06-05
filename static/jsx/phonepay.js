/** @jsx React.DOM */

var React = require('react/addons');
var superagent = require('superagent');
var $ = window.jQuery = require('jquery');

require('./jquery.velocity.min');
require('./velocity.ui');

var Button = React.createClass({
  showForm: function() {
    this.props.form.show(this.props.options);
  },
  render: function() {
    return (
      <button
        className="phonepay-button"
        onClick={this.showForm}
        >
        Buy
      </button>
    );
  }
});

var Form = React.createClass({
  getInitialState: function() {
    return {
      options: {
        header: 'PHonePay',
        currency: 'PHP',
        button: 'Pay with Globe Load'
      },
      hidden: true,
      step: 'number',
      dialogUrl: null,
      lastNumber: ''
    };
  },
  show: function(options) {
    options = $.extend(this.state.options, options);
    this.setState({
      options: options,
      hidden: false,
      step: 'number'
    });
  },
  hide: function() {
    this.setState({hidden: true});
  },
  pay: function() {
    var number = this.refs.number.getDOMNode().value;
    var options = this.state.options;
    var $pay = $(this.refs.pay.getDOMNode())
    superagent
      .post('/charge')
      .send({
        subscriber_number: number,
        amount: options.amount
      })
      .end((function(res) {
        if (res.body.confirm_code_sent) {
          this.showConfirm();
        }
        if (res.body.needs_authorization) {
          this.showAuthorize(res.body.dialog_url);
        }
        $pay.prop('disabled', false);
      }).bind(this));
    this.setState({lastNumber: number});
    $pay.prop('disabled', true);
  },
  showAuthorize: function(url) {
    this.setState({
      step: 'authorize',
      dialogUrl: url
    });
  },
  showConfirm: function() {
    this.setState({
      step: 'confirm'
    });
  },
  componentDidUpdate: function(prevProps, prevState) {
    if (!this.state.hidden) {
      switch (this.state.step) {
        case 'number':
          setTimeout((function() {
            $(this.refs.number.getDOMNode())
              .focus();
          }).bind(this), 1);
          break;
        case 'confirm':
          setTimeout((function() {
            $(this.refs.confirmCode.getDOMNode())
              .focus();
          }).bind(this), 1);
          break;
      }
      if (this.state.hidden != prevState.hidden) {
        $(this.refs.overlay.getDOMNode())
          .velocity('fadeIn', 200);
        $(this.getDOMNode()).find('p')
          .velocity('transition.slideUpBigIn', {
            stagger: 100,
            duration: 500
          });
        $(this.refs.box.getDOMNode())
          .velocity('transition.expandIn', 500);
      }
      if (this.state.step != prevState.step) {
        $(this.refs.box.getDOMNode())
          .velocity('transition.expandIn', 500);
      }
    }
  },
  render: function() {
    var className = React.addons.classSet({
      'phonepay-form': true,
      'hidden': this.state.hidden,
    });
    var options = this.state.options;
    var box = [];
    switch (this.state.step) {
      case 'number':
        box.push(
          <p>
            <label>
              Cellphone Number
              <input
                key="number"
                ref="number"
                type="text"
                placeholder="e.g. 9171234567"
                defaultValue={this.state.lastNumber}
              />
            </label>
          </p>
        );
        box.push(
          <p>
            <button
              ref="pay"
              onClick={this.pay}
              >
              {options.button}
            </button>
          </p>
        );
        break;
      case 'authorize':
        box.push(
          <p className="authorize-instructions">
            Hello new user! Please authorize
            with Globe first to proceed.
          </p>
        );
        box.push(
          <p>
            <a
              href={this.state.dialogUrl}
              ref="authorize"
              target="_blank"
              onClick={(function(){this.show()}).bind(this)}
              >
              Authorize
            </a>
          </p>
        );
        break;
      case 'confirm':
        box.push(
          <p>
            <label>
              Confirmation Code
              <input
                key="confirmCode"
                ref="confirmCode"
                type="text"
                placeholder="e.g. 123456"
              />
            </label>
          </p>
        );
        box.push(
          <p>
            <button
              ref="confirm"
              onClick={this.confirm}
              >
              Confirm Payment
            </button>
          </p>
        );
        break;
    }
    return (
      <div className={className}>
        <div
          ref="overlay"
          className="overlay"
          onClick={this.hide}
        />
        <div
          ref="box"
          className="box"
          >
          <h2>{options.header}</h2>
          <p className="details">
            {options.desc} <span className="amount">({options.currency}{options.amount})</span>
          </p>
          {box}
          <p className="powered-by">
            Powered by PHonePay
          </p>
        </div>
      </div>
    );
  }
});

var container = document.createElement('div');
document.body.appendChild(container);

var form = React.renderComponent(
  <Form />,
  container
);

window.pp = function(options) {
  options = $.extend(form.state.options, options);
  form.setState({
    options: options
  });
};

Array.prototype.forEach.call(
  document.querySelectorAll('.phonepay'),
  function(el) {
    React.renderComponent(
      <Button
        form={form}
        options={el.dataset}
      />,
      el
    );
  }
);

